import ctypes
from ctypes import wintypes
from models import FileExtent
from ntfs import NTFSDisk
from shims import CloseHandle, CreateFile


def copy_file(source_file: str, destination_file: str) -> None:
    FILE_READ_ATTR = 0x00000080
    FILE_NO_BUF = 0x20000000
    FILE_FLAG_SYS = 0x00000004
    ACCESS_READ: int = 0x80000000
    SHARE_RW: int = 0x00000001 | 0x00000002
    MODE_OPEN: int = 0x00000003
    ATTR_NORMAL: int = 0x80

    # Open the source file
    handle: wintypes.HANDLE = CreateFile(
        source_file,
        ACCESS_READ,
        SHARE_RW,
        None,
        MODE_OPEN,
        FILE_NO_BUF | FILE_FLAG_SYS,
        None,
    )

    if handle == -1:
        raise ctypes.WinError(ctypes.get_last_error())

    drive_letter = source_file[0]

    with NTFSDisk(drive_letter=drive_letter) as disk:
        extents: list[FileExtent] = disk.get_retrieval_pointers(handle)
        total_size: int = sum(extent.size for extent in extents)
        copied_bytes: int = 0

        with open(destination_file, "wb") as dest_file:
            for extent in extents:
                for offset in range(0, extent.size, 10000):
                    current_size = min(10000, extent.size - offset)
                    data: bytes = disk.read_clusters(
                        extent.lcn + offset,
                        current_size,
                    )
                    dest_file.write(data)
                    copied_bytes += current_size

    if not CloseHandle(handle):
        raise ctypes.WinError(ctypes.get_last_error())

    if copied_bytes != total_size:
        raise ValueError("Not all bytes were copied.")
