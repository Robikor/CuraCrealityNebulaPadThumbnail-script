# Cura Creality Nebula Pad Thumbnail creator
#
# This only works with Cura 5.0+

import base64

from UM.Logger import Logger
from cura.Snapshot import Snapshot
from PyQt6.QtCore import QByteArray, QIODevice, QBuffer

from ..Script import Script

class CreateCrealityNebulaPadThumbnail(Script):
    def __init__(self):
        super().__init__()

    def _createSnapshot(self, width, height):
        Logger.log("d", "Creating thumbnail image...")
        try:
            return Snapshot.snapshot(width, height)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")

    def _encodeSnapshot(self, snapshot):
        Logger.log("d", "Encoding thumbnail image...")
        try:
            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            thumbnail_image = snapshot
            thumbnail_image.save(thumbnail_buffer, "PNG")
            thumbnail_data = thumbnail_buffer.data()
            thumbnail_length = thumbnail_data.length()
            base64_bytes = base64.b64encode(thumbnail_data)
            base64_message = base64_bytes.decode('ascii')
            thumbnail_buffer.close()
            Logger.log("d", "Snapshot thumbnail_length={}".format(thumbnail_length))
            return (base64_message, thumbnail_length)
        except Exception:
            Logger.logException("w", "Failed to encode snapshot image")

    def _convertSnapshotToGcode(self, thumbnail_length, encoded_snapshot, width, height, chunk_size=78):
        Logger.log("d", "Converting snapshot into gcode...")
        gcode = []

        # these numbers appear to be related to image size, guessing here
        x1 = (int)(width/80) + 1
        x2 = width - x1
        header = "; png begin {}*{} {} {} {} {}".format(width, height, thumbnail_length, x1, x2, 500)
        Logger.log("d", "Gcode header={}".format(header))
        gcode.append(header)

        chunks = ["; {}".format(encoded_snapshot[i:i+chunk_size])
                  for i in range(0, len(encoded_snapshot), chunk_size)]
        gcode.extend(chunks)

        gcode.append("; png end")

        return gcode

    def _convertSnapshotToThumbnailGcode(self, encoded_snapshot, width, height, chunk_size=78):
        Logger.log("d", "Converting snapshot into thumbnail gcode...")
        gcode = []

        encoded_snapshot_length = len(encoded_snapshot)
        gcode.append(";")
        gcode.append("; thumbnail begin {}x{} {}".format(width, height, encoded_snapshot_length))

        chunks = ["; {}".format(encoded_snapshot[i:i+chunk_size])
                  for i in range(0, len(encoded_snapshot), chunk_size)]
        gcode.extend(chunks)

        gcode.append("; thumbnail end")
        gcode.append(";")
        gcode.append("")

        return gcode

    def getSettingDataString(self):
        return """{
            "name": "Create Creality Nebula Pad Thumbnail",
            "key": "CreateCrealityNebulaPadThumbnail",
            "metadata": {},
            "version": 2,
            "settings":
            {}
        }"""

    def execute(self, data):
        width1 = 96
        height1 = 96
        width2 = 300
        height2 = 300
        Logger.log("d", "CreateCrealityNebulaPadThumbnail Plugin start")

        snapshot1 = self._createSnapshot(width1, height1)
        snapshot2 = self._createSnapshot(width2, height2)
        if snapshot1 and snapshot2:
            Logger.log("d", "Snapshots created")
            (encoded_snapshot, thumbnail_length) = self._encodeSnapshot(snapshot1)
            snapshot_gcode1 = self._convertSnapshotToGcode(thumbnail_length, encoded_snapshot, width1, height1)
            snapshot_gcode2 = self._convertSnapshotToThumbnailGcode(encoded_snapshot, width1, height1)
            (encoded_snapshot, thumbnail_length) = self._encodeSnapshot(snapshot2)
            snapshot_gcode3 = self._convertSnapshotToGcode(thumbnail_length, encoded_snapshot, width2, height2)
            snapshot_gcode4 = self._convertSnapshotToThumbnailGcode(encoded_snapshot, width2, height2)

            Logger.log("d", "Layer count={}".format(len(data)))
            if len(data) > 0:
                # The Creality Nebula Pad really wants this at the top of the file
                layer_index = 0
                lines = data[layer_index].split("\n")
                Logger.log("d", "Adding snapshot1 gcode lines (len={})".format(len(snapshot_gcode1)))
                Logger.log("d", "Adding snapshot2 gcode lines (len={})".format(len(snapshot_gcode2)))
                Logger.log("d", "Adding snapshot3 gcode lines (len={})".format(len(snapshot_gcode3)))
                Logger.log("d", "Adding snapshot4 gcode lines (len={})".format(len(snapshot_gcode4)))
                lines[0:0] = snapshot_gcode1 + snapshot_gcode3 + snapshot_gcode2 + snapshot_gcode4
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines

        Logger.log("d", "CreateCrealityNebulaPadThumbnail Plugin end")
        return data