class StageDoesNotExist(Exception): pass


class Stage(object):

    ordered_stages = []

    def __init__(self, stage=None):
        num_stages = len(self.ordered_stages)
        if num_stages == 0 or num_stages % 2 != 0:
            raise AttributeError('Invalid number of stages: %d' % num_stages)

        if stage is None:
            self.reset()
        else:
            self._stage = stage

        try:
            self._get_index(self._stage)
        except ValueError:
            raise StageDoesNotExist('Stage does not exist: %s' % self._stage)

    @property
    def name(self):
        """Return current stage name"""
        return self._stage

    @property
    def is_processing_stage(self):
        """Return True if current stage is processing stage.
        Otherwise, return False.
        """
        index = self._get_index(self._stage)
        return index % 2 == 0

    def reset(self):
        """Reset current stage to initial stage"""
        self._stage = self.ordered_stages[0]

    def next(self):
        """Return next stage"""
        index = self._get_index(self._stage)
        try:
            return self.__class__(self.ordered_stages[index+1])
        except IndexError:
            raise StageDoesNotExist('Next stage does not exist')

    def previous(self):
        """Return previous stage"""
        index = self._get_index(self._stage)
        if index == 0:
            raise StageDoesNotExist('Previous stage does not exist')
        return self.__class__(self.ordered_stages[index-1])

    def previous_completed(self):
        """Return previous completed stage"""
        index = self._get_index(self._stage)
        if index % 2 == 0:
            index -= 1
        else:
            index -= 2
        if index < 0:
            raise StageDoesNotExist('Previous completed stage does not exist')
        return self.__class__(self.ordered_stages[index])

    def previous_processing(self):
        """Return previous processing stage"""
        index = self._get_index(self._stage)
        if index % 2 == 0:
            index -= 2
        else:
            index -= 1
        if index < 0:
            raise StageDoesNotExist('Previous processing stage does not exist')
        return self.__class__(self.ordered_stages[index])

    def next_processing(self):
        """Return next processing stage"""
        index = self._get_index(self._stage)
        if index % 2 == 0:
            index += 2
        else:
            index += 1
        try:
            return self.__class__(self.ordered_stages[index])
        except IndexError:
            raise StageDoesNotExist('Next processing stage does not exist')

    def _get_index(self, stage_name):
        return self.ordered_stages.index(stage_name)


class TorrentStage(Stage):

    ordered_stages = [
        'Packaging', 'Packaged',
        'Listing', 'Listed',
        'Downloading', 'Downloaded',
        'Extracting', 'Extracted',
        'Sorting', 'Completed',
        'Deleting', 'Deleted',
    ]


class PackageFileStage(Stage):

    ordered_stages = [
        'Adding', 'Added',
        'Downloading', 'Downloaded',
        'Deleting', 'Deleted',
    ]
