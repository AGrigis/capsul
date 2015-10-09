#! /usr/bin/env python
##########################################################################
# CAPSUL - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import numpy

# Capsul import
from capsul.utils.trait_utils import clone_trait
from capsul.utils.trait_utils import is_trait_pathname
from capsul.utils.trait_utils import trait_ids
from capsul.utils.trait_utils import allow_none_trait_values
from capsul.utils.topological_sort import GraphNode
from capsul.utils.topological_sort import Graph

# Soma import
from soma.controller import Controller
from soma.controller.controller import ControllerTrait

# Trait import
from traits.api import Undefined
from traits.api import Event


class IProcess(Controller):
    """ An iterative box that may be used to iterate over a building box.
    """
    iterprefix = "iter"
    itersep = "#"

    def __init__(self, process, iterinputs=None, iteroutputs=None):
        """ Initialize the Ibox class.

        Parameters
        ----------
        process: instance
            a process/interface instance.
        iterinputs: list of str (optional, default None)
            the list of iterative input controls.
        iteroutputs: list of str (optional, default None)
            the list of iterative output controls.
        """
        # Define class parameters
        self.iterinputs = iterinputs or []
        self.iteroutputs = iteroutputs or []
        self.ispbox = False
        self.iterbox = process
        if "Pipeline" in [klass.__name__ for klass in process.__class__.__mro__]:
            self.ispbox = True
        self.active = True
        self._states = {}

        # Create the bbox name
        self.name = self.iterprefix + self.iterbox.name
        self.id = self.iterprefix + self.iterbox.id

        # Inherit to create trait controller
        super(IProcess, self).__init__()

        # Create the input and output controls
        self._set_controls()

    def __call__(self, *args, **kwargs):
        """ Execute the IProcess class.
        """
        # Prepare outputs
        generated_iteroutputs = {}
        generated_outputs = {}
        for control_name in self.iterbox.traits(output=True):
            if control_name in self.iteroutputs:
                generated_iteroutputs[control_name] = []
            else:
                generated_outputs[control_name] = []

        # Parametrize the iterative bbox input parameters
        graphs = self.itergraphs()
        for iteration in range(len(graphs)):

            # Get iteration parameters
            box_name = "#{0}".format(iteration)
            graph = graphs[box_name]

            # Execute the box
            box = self.iterbox
            self.load_state(box_name)
            box(*args, **kwargs)
            for control_name, value in box.get_outputs().items():
                if control_name in generated_iteroutputs:
                    generated_iteroutputs[control_name].append(value)
                else:
                    generated_outputs[control_name].append(value)

        # Set outputs
        for control_name, value in generated_outputs.items():
            if len(value) > 0 and (numpy.asarray(value) == value[0]).all():
                setattr(self, control_name, value[0])
            else:
                raise ValueError("Impossible to set the regular output control "
                    "'{0}' defined in the iterative box, arguments in '{1}' "
                    "are different or empty.".format(control_name, value)) 
        for control_name, value in generated_iteroutputs.items():
            setattr(self, self.iterprefix + control_name, value)

    ###########################################################################
    # Public Members
    ###########################################################################

    def add_trait(self, name, *trait):
        """ Add a new trait allowing None values during the validation.

        Parameters
        ----------
        name: str (mandatory)
            the trait name.
        trait: traits.api (mandatory)
            a valid trait.
        """
        # Save the default value
        default = trait[0].defaultvalue

        # Allow None as a trait value
        if self.is_user_trait(trait[0]):
            allow_none_trait_values(trait[0])

        # Inheritance: create the instance trait attribute
        super(IProcess, self).add_trait(name, *trait)

        # Set the trait default value
        self.trait(name).defaultvalue = default

    def is_user_trait(self, trait):
        """ Method that evaluate if a trait is a user parameter
        (i.e. not an Event or ControllerTrait).

        Parameters
        ----------
        trait: Trait (mandatory)
            a trait.

        Returns
        -------
        out: bool
            True if the trait is a user trait,
            False otherwise.
        """
        return not (isinstance(trait.handler, Event) or
                    isinstance(trait.handler, ControllerTrait))

    def dump_state(self, node_name):
        """ Update the image of the iterative box state.

        Parameters
        ----------
        node_name: str (mandatory)
            the name of the state to update.
        """
        if node_name not in self._states:
            raise ValueError(
                "'{0}' is not a valid state. State value must be in "
                "'{1}'.".format(node_name, self._states.keys()))
        self._states[node_name] = self.iterbox.dump_state()

    def load_state(self, node_name):
        """ Restore the iterative box state.

        Parameters
        ----------
        node_name: str (mandatory)
            the name of the state to restore.
        """
        if node_name not in self._states:
            raise ValueError(
                "'{0}' is not a valid state. State value must be in "
                "'{1}'.".format(node_name, self._states.keys()))
        self.iterbox.load_state(self._states[node_name])  

    def update_iteroutputs(self, iterboxes):
        """ Update the IProcess standard/iterative output control values.

        Parameters
        ----------
        iterboxes: list of str (mandatory)
            the sorted executed iterative boxe names used to update the ibox
            outputs.
        """
        # Update all the ibox outputs
        for control_name in self.traits(output=True):

            # Get the non iterative control name and the iterative boxes
            # outputs
            control_name = control_name.replace(self.iterprefix, "")
            itervalue = [
                self._states[box_name]["__self_outputs__"][control_name]
                for box_name in iterboxes]

            # Update the ibox outputs: a standard ibox control is set only if
            # all the iterative jobs have returned the same value
            if control_name in self.iteroutputs:
                itercontrol_name = self.iterprefix + control_name
                setattr(self, itercontrol_name, itervalue)
            else:
                if all(value == itervalue[0] for value in itervalue):
                    setattr(self, control_name, itervalue[0])
                else:
                    raise ValueError(
                        "The '{0}' standard ibox output can't have different "
                        "values {1}.".format(control_name, itervalue))

    def itergraphs(self, prefix=""):
        """ Create a list of iterative pipeline's graph representations.

        Parameters
        ----------
        prefix: str (optional, default '')
            a prefix for the box names.

        Returns
        -------
        itergraphs: dictionary
            the iterative pipeline's graph representations. Each value is
            contains a graph.
        """
        # Update the iterative pipeline only if all the input terative
        # controls have the same number of elements
        nb_of_elements = []
        for control_name in self.iterinputs:
            itercontrol_name = self.iterprefix + control_name
            itervalue = getattr(self, itercontrol_name)
            if itervalue is []:
                return {}
            nb_of_elements.append(len(itervalue))
        nb_of_elements = numpy.asarray(nb_of_elements)
        nb_of_inputs = nb_of_elements.max()
        is_valid = (nb_of_elements == nb_of_inputs).all()

        # Update the iterative graphs
        itergraphs = {}
        if is_valid:

            # Create the requested number of graphs
            self._states = {}
            for iteritem in range(nb_of_inputs):

                # Parametrize the iterative box and save the current state
                for control_name in self.iterinputs:
                    itercontrol_name = self.iterprefix + control_name
                    value = getattr(self, itercontrol_name)
                    setattr(self.iterbox, control_name, value[iteritem])
                for control_name in self.traits(output=False):
                    if control_name not in self.iterinputs:
                        setattr(self.iterbox, control_name,
                                getattr(self, control_name))

                node_name = "{0}{1}{2}".format(prefix, self.itersep, iteritem)
                # Iterate on a pipeline
                if self.ispbox:
                    itergraph, _, _ = self.iterbox._create_graph(
                        self.iterbox, prefix=node_name + ".",
                        filter_inactive=True)
                # Iterate on a process
                else:
                    itergraph = Graph()
                    itergraph.add_node(GraphNode(node_name, self.iterbox))
                itergraphs[node_name] = itergraph

                # Save the current pipeline state
                self._states[node_name] = self.iterbox.dump_state()

        return itergraphs

    def set_parameter(self, name, value):
        """ Method to set an iterative process instance trait value.

        For File and Directory traits the None value is replaced by the
        special Undefined trait value.

        Parameters
        ----------
        name: str (mandatory)
            the trait name we want to modify.
        value: object (mandatory)
            the trait value we want to set.
        """
        # Detect File and Directory trait types with None value
        if value is Undefined and is_trait_pathname(self.trait(name)):
            value = None

        # Set the new trait value
        setattr(self, name, value)

    def get_inputs(self):
        """ Method to access the process inputs.

        Returns
        -------
        outputs: dict
            a dictionary with all the input trait names and values.
        """
        output = {}
        for trait_name, trait in self.traits(output=False).iteritems():
            output[trait_name] = getattr(self, trait_name)
        return output

    def get_outputs(self):
        """ Method to access the process outputs.

        Returns
        -------
        outputs: dict
            a dictionary with all the output trait names and values.
        """
        output = {}
        for trait_name, trait in self.traits(output=True).iteritems():
            output[trait_name] = getattr(self, trait_name)
        return output

    ###########################################################################
    # Private Members
    ###########################################################################

    def _set_controls(self):
        """ Define the iprocess input and output parameters.

        These parameters are defined in the list of iterative controls and
        built from the building box controls: add a 'List' extra level to
        create an iterative parameter.
        """
        # Build input iterative controls
        for control_name in self.iterinputs:

            # Check that the iterative control is defined in the building box
            if control_name not in self.iterbox.traits(output=False):
                raise ValueError(
                    "Impossible to build IProcess '{0}': '{1}' input iterative "
                    "control type is not defined in iterative building box. "
                    "Allowed inputs are {2}.".format(
                        self.id, control_name,
                        self.iterbox.user_traits().keys()))

            # Create the iterative control
            trait = self.iterbox.trait(control_name)
            trait_desc = trait.desc
            trait_description = trait_ids(trait)
            itertrait_description = ["List_" + x for x in trait_description]
            itername = "{0}{1}".format(self.iterprefix, control_name)
            trait = clone_trait(itertrait_description)
            self.add_trait(itername, trait)
            self.trait(itername).output = False
            self.trait(itername).optional = False
            self.trait(itername).desc = trait_desc

        # Build output iterative controls
        for control_name in self.iteroutputs:

            # Check that the iterative control is defined in the building box
            if control_name not in self.iterbox.traits(output=True):
                raise ValueError(
                    "Impossible to build IProcess '{0}': '{1}' outputs iterative "
                    "control type is not defined in iterative building box. "
                    "Allowed outputs are {2}.".format(
                        self.id, control_name,
                        self.iterbox.user_traits().keys()))

            # Create the iterative control
            trait = self.iterbox.trait(control_name)
            trait_desc = trait.desc
            trait_description = trait_ids(trait)
            itertrait_description = ["List_" + x for x in trait_description]
            itername = "{0}{1}".format(self.iterprefix, control_name)
            trait = clone_trait(itertrait_description)
            self.add_trait(itername, trait)
            self.trait(itername).output = True
            self.trait(itername).optional = False
            self.trait(itername).desc = trait_desc

        # Copy the input/output controls to the iterative box interface
        for control_name in self.iterbox.traits(output=False):
            if (control_name not in self.iterinputs and
                    control_name != "selection_changed"):
                trait = self.iterbox.trait(control_name)
                self.add_trait(control_name, trait)
                setattr(self, control_name, getattr(self.iterbox, control_name))
        for control_name in self.iterbox.traits(output=True):
            if (control_name not in self.iteroutputs and
                    control_name != "selection_changed"):
                trait = self.iterbox.trait(control_name)
                self.add_trait(control_name, trait)
