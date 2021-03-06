import logging
from vfs.engine import VFS
from vfs.physicalvideo import PhysicalVideo


class LogicalVideo(object):
    DEFAULT_ENCODED_BUDGET_MULTIPLIER = 10.0
    DEFAULT_RAW_BUDGET_MULTIPLIER = 1.0

    @classmethod
    def add(cls, name):
        return LogicalVideo(VFS.instance().database.execute(
            'INSERT INTO logical_videos(name) VALUES (?)', name).lastrowid, name)

    @classmethod
    def get(cls, id):
        return LogicalVideo(*VFS.instance().database.execute(
            'SELECT id, name FROM logical_videos WHERE id = ?', id).fetchone())

    @classmethod
    def get_all(cls):
        return map(lambda args: LogicalVideo(*args), VFS.instance().database.execute(
            'SELECT id, name FROM logical_videos').fetchall())

    @classmethod
    def get_by_name(cls, name):
        return LogicalVideo(*VFS.instance().database.execute(
            'SELECT id, name  FROM logical_videos WHERE name = ?', name).fetchone())

    @classmethod
    def exists_by_name(cls, name):
        return VFS.instance().database.execute(
            'SELECT 1 FROM logical_videos WHERE name = ? LIMIT 1', name).fetchone() is not None

    @classmethod
    def delete(cls, logical_video):
        logging.info('Deleting Video %d', logical_video.id)

        for video in logical_video.videos():
            PhysicalVideo.delete(video)

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self._budget = None
        self._duration = None
        self._videos = None
        self._physical_constraints = None

    def videos(self):
        if self._videos is None:
            self._videos = list(map(lambda args: PhysicalVideo(*args),
                       VFS.instance().database.execute(
                           'SELECT id, logical_id, height, width, codec, filename, headers, gop_size, mdat_offset FROM physical_videos WHERE logical_id = ?', self.id).fetchall()))
        return self._videos

    def duration(self):
        if self._duration is None:
            self._duration = VFS.instance().database.execute(
                           'SELECT MAX(end_time) '
                           'FROM physical_videos '
                           'INNER JOIN gops ON physical_videos.id = gops.physical_id '
                           'WHERE logical_id = ?', self.id).fetchone()[0]
        return self._duration

    @property
    def budget(self):
        if self._budget is None:
            self._budget = VFS.instance().database.execute('SELECT budget FROM logical_videos WHERE id = ?', self.id).fetchone()[0]
        return self._budget

    @budget.setter
    def budget(self, value):
        VFS.instance().database.execute('UPDATE logical_videos SET budget = ? WHERE id = ?', (value, self.id))
        self._budget = value
        logging.debug('Logical video %s has budget %dMB', self.name, value // (1000*1000))

"""
    def get_physical_constraints(self, resolution, t):
        if (resolution, t) in self._physical_constraints is None:
            self._physical_constraints = VFS.instance().database.execute(
            'SELECT physical_videos.id, MIN(start_time), MAX(end_time), codec, height, width, SUM(size), MAX(fps) '
            'FROM gops, physical_videos '
            'WHERE logical_id = ? AND '
            '      height >= ? AND width >= ? AND '
            '      start_time < ? AND end_time >= ? AND '
            '      gops.physical_id = physical_videos.id '
            'GROUP BY physical_videos.id',
                (self.id,
                resolution[0], resolution[1],
                t[1] if t is not None else 9999999,
                t[0] if t is not None else -1)).fetchall()
        return self._physical_constraints
"""