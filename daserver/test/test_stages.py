from django.test import TestCase

from dasdapi.stages import Stage, StageDoesNotExist


class TestStage(Stage):

    ordered_stages = [
        'P1', 'C1',
        'P2', 'C2',
        'P3', 'C3'
    ]


class StagesTests(TestCase):

    def test_init(self):
        stage = TestStage()
        self.assertEqual(stage.name, 'P1')
        stage = TestStage('C1')
        self.assertEqual(stage.name, 'C1')
        stage = TestStage('P2')
        self.assertEqual(stage.name, 'P2')
        stage = TestStage('C2')
        self.assertEqual(stage.name, 'C2')
        stage = TestStage('P3')
        self.assertEqual(stage.name, 'P3')
        stage = TestStage('C3')
        self.assertEqual(stage.name, 'C3')
        with self.assertRaises(StageDoesNotExist):
            stage = TestStage('DoesNotExist')

    def test_is_processing_stage(self):
        stage = TestStage('P1')
        self.assertTrue(stage.is_processing_stage)
        stage = TestStage('C1')
        self.assertFalse(stage.is_processing_stage)
        stage = TestStage('P2')
        self.assertTrue(stage.is_processing_stage)
        stage = TestStage('C2')
        self.assertFalse(stage.is_processing_stage)

    def test_linear_order(self):
        stage = TestStage()
        self.assertEqual(stage.name, 'P1')
        stage = stage.next()
        self.assertEqual(stage.name, 'C1')
        stage = stage.next()
        self.assertEqual(stage.name, 'P2')
        stage = stage.next()
        self.assertEqual(stage.name, 'C2')
        stage = stage.next()
        self.assertEqual(stage.name, 'P3')
        stage = stage.next()
        self.assertEqual(stage.name, 'C3')

    def test_lower_bounds(self):
        stage = TestStage()
        with self.assertRaises(StageDoesNotExist):
            stage.previous()

    def test_upper_bounds(self):
        stage = TestStage('C3')
        with self.assertRaises(StageDoesNotExist):
            stage.next()

    def test_previous_completed(self):
        stage = TestStage()
        with self.assertRaises(StageDoesNotExist):
            stage = stage.previous_completed()

        stage = TestStage('P1')
        with self.assertRaises(StageDoesNotExist):
            stage = stage.previous_completed()
        stage = TestStage('C1')
        with self.assertRaises(StageDoesNotExist):
            stage = stage.previous_completed()

        stage = TestStage('P2')
        stage = stage.previous_completed()
        self.assertEqual(stage.name, 'C1')
        stage = TestStage('P3')
        stage = stage.previous_completed()
        self.assertEqual(stage.name, 'C2')

        stage = TestStage('C2')
        stage = stage.previous_completed()
        self.assertEqual(stage.name, 'C1')
        stage = TestStage('C3')
        stage = stage.previous_completed()
        self.assertEqual(stage.name, 'C2')

    def test_previous_processing(self):
        stage = TestStage()
        with self.assertRaises(StageDoesNotExist):
            stage = stage.previous_processing()

        stage = TestStage('P1')
        with self.assertRaises(StageDoesNotExist):
            stage = stage.previous_processing()

        stage = TestStage('C1')
        stage = stage.previous_processing()
        self.assertEqual(stage.name, 'P1')
        stage = TestStage('C2')
        stage = stage.previous_processing()
        self.assertEqual(stage.name, 'P2')

        stage = TestStage('P2')
        stage = stage.previous_processing()
        self.assertEqual(stage.name, 'P1')
        stage = TestStage('P3')
        stage = stage.previous_processing()
        self.assertEqual(stage.name, 'P2')

    def test_next_processing(self):
        stage = TestStage()
        stage = stage.next_processing()
        self.assertEqual(stage.name, 'P2')
        stage = stage.next_processing()
        self.assertEqual(stage.name, 'P3')
        with self.assertRaises(StageDoesNotExist):
            stage.next_processing()

        stage = TestStage('C1')
        stage = stage.next_processing()
        self.assertEqual(stage.name, 'P2')

        stage = TestStage('P2')
        stage = stage.next_processing()
        self.assertEqual(stage.name, 'P3')

    def test_invalid_stages_len(self):
        """Add stage to make an odd number of stages"""
        TestStage.ordered_stages.append('BadStage')
        with self.assertRaises(AttributeError):
            TestStage()
        del TestStage.ordered_stages[-1]
