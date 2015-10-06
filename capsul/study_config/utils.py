#! /usr/bin/env python
##########################################################################
# CAPSUL - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

from capsul.process import IProcess


def split_name(process_name):
    """ Split a process name.

    Parameters
    ----------
    process_name: str (mandatory)
        the process flatten name.

    Returns
    -------
    identifier: int
        the execution identifier.
    box_name: str
        the box flatten name.
    box_exec_name: str
        if an iterative box is detected returned his execution id,
        None otherwise.
    box_iter_name: str
        if an iterative box is detected returned his id, None otherwise.
    iteration: int
        if an iterative box is detected returned his iteration number,
        None otherwise.
    """
    identifier, box_name = process_name.split("-")
    identifier = int(identifier)
    if IProcess.itersep in box_name:
        id_items = box_name.split(IProcess.itersep)
        if len(id_items) == 2:
            box_iter_name, iter_id = id_items
        else:
            box_iter_name = IProcess.itersep.join(id_items[:-1])
            iter_id = id_items[-1]         
        iteration = iter_id.split(".")[0]
        box_exec_name = box_iter_name + IProcess.itersep + iteration
        iteration = int(iteration)
    else:
        box_exec_name = None
        box_iter_name = None
        iteration = None
    return identifier, box_name, box_exec_name, box_iter_name, iteration
