#!/usr/bin/env python

import unittest
from capsul.study_config.study_config import StudyConfig
from capsul.study_config.config_modules.fom_config import FomConfig
from soma.application import Application

class TestStudyConfigFOM(unittest.TestCase):

    def setUp(self):
        pass

    def test_study_config_fom(self):
        initial_config = {
          "input_directory" : "/blop/basetests",
          "output_directory" : "/blop/basetests",
          "input_fom" : "morphologist-auto-1.0",
          "output_fom" : "morphologist-auto-1.0",
          "shared_fom" : "shared-brainvisa-1.0",
          "spm_directory" : "/i2bm/local/spm8-standalone",
          "use_soma_workflow" : True,
          "use_fom" : True,
        }

        soma_app = Application('soma.fom', '1.0')
        soma_app.plugin_modules.append('soma.fom')
        soma_app.initialize()
        study_config = StudyConfig(
            modules=StudyConfig.default_modules + [FomConfig])
        study_config.set_study_configuration(initial_config)
        FomConfig.check_and_update_foms(study_config)
        self.assertTrue(hasattr(study_config.modules_data, 'foms'))
        self.assertTrue(hasattr(study_config.modules_data, 'fom_atp'))
        self.assertTrue(hasattr(study_config.modules_data, 'fom_pta'))
        self.assertTrue(len(study_config.modules_data.foms) == 3)
        self.assertTrue(len(study_config.modules_data.fom_atp) == 3)
        self.assertTrue(len(study_config.modules_data.fom_pta) == 3)


def test():
    """ Function to execute unitest
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudyConfigFOM)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    print("RETURNCODE: ", test())
