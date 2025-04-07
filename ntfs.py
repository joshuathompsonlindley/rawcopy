import ctypes
from ctypes import wintypes
from typing import Any

from shims import CreateFile, GetFreeDiskSpace, DeviceIoControl, CloseHandle, SetFilePointer, ReadFile
from models import (
    DiskGeometry,
    GetLengthInformation,
    RetrievalPointerExtent,
    RetrievalPointersBuffer,
    StartingVcnInputBuffer,
    FileExtent,
)


class NTFSDisk:
    def __init__(self, drive_letter: str):
        # DOS device name for the disk
        self.disk_path: str = f"\\\.\{drive_letter}:"

        # Win32 handle to the disk
        self.handle: wintypes.HANDLE

        # FS information, gets populated when the disk is opened
        self.size_bytes: int
        self.cluster_size: int
        self.sector_size: int
        self.sectors_per_cluster: int

        # FS information, can get calculated from the above
        self.cluster_count: int = self.size_bytes // self.cluster_size
        self.sector_count: int = self.size_bytes // self.sector_size

        # Current position in the stream
        self.current_position: int = 0

        # Open the disk
        self._initialise_disk()

        # Get disk geometry
        self._get_disk_geometry()

        # Get disk length
        self._get_disk_length()

        # Get cluster count
        self._get_cluster_count()

    def __enter__(self) -> None:
        """
        Enter the context manager.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit the context manager.
        Close the disk handle.
        """
        if self.handle:
            # Set the handle to None to avoid double closing
            self.handle = None

            if not CloseHandle(self.handle):
                raise ctypes.WinError(ctypes.get_last_error())

    def _initialise_disk(self) -> None:
        """
        Open the disk for reading.
        The disk path is in the format \\.\X: where X is the drive letter.
        """
        ACCESS_READ: int = 0x80000000
        SHARE_RW: int = 0x00000001 | 0x00000002
        MODE_OPEN: int = 0x00000003
        ATTR_NORMAL: int = 0x80

        # Open the disk
        handle: wintypes.HANDLE = CreateFile(self.disk_path, ACCESS_READ, SHARE_RW, None, MODE_OPEN, ATTR_NORMAL, None)

        # Check if the handle is valid and raise an error if not
        if handle == -1:
            raise ctypes.WinError(ctypes.get_last_error())

        self.handle = handle

    def _get_disk_geometry(self) -> None:
        """
        Get the disk geometry, which includes the number of cylinders, media type, tracks per cylinder,
        sectors per track, and bytes per sector.

        The disk geometry is used to calculate the size of the disk and the number of sectors.
        """
        disk_geometry: DiskGeometry = DiskGeometry()
        ioctl_get_disk_geometry: int = 0x00070000

        # Get the disk geometry and raise an error if it fails
        if not DeviceIoControl(
            self.handle,
            ioctl_get_disk_geometry,
            None,
            0,
            ctypes.byref(disk_geometry),
            ctypes.sizeof(disk_geometry),
            wintypes.DWORD(),
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        self.sector_size = disk_geometry.BytesPerSector

    def _get_disk_length(self) -> None:
        """
        Get the length of the disk in bytes.

        The length is used to calculate the size of the disk and the number of clusters.
        """
        disk_length: GetLengthInformation = GetLengthInformation()
        ioctl_get_disk_length_info: int = 0x0007405C

        # Get the disk length and raise an error if it fails
        if not DeviceIoControl(
            self.handle,
            ioctl_get_disk_length_info,
            None,
            0,
            ctypes.byref(disk_length),
            ctypes.sizeof(disk_length),
            wintypes.DWORD(),
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        self.size_bytes = disk_length.Length

    def _get_cluster_count(self) -> None:
        """
        Get the cluster count of the disk.

        The cluster count is used to calculate the size of the disk and the number of sectors.
        """
        sectors_per_cluster: wintypes.DWORD = wintypes.DWORD()
        bytes_per_sector: wintypes.DWORD = wintypes.DWORD()

        # Get the cluster size and raise an error if it fails
        if not GetFreeDiskSpace(
            self.disk_path,
            ctypes.byref(sectors_per_cluster),
            ctypes.byref(bytes_per_sector),
            wintypes.DWORD(),
            wintypes.DWORD(),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        self.cluster_size = bytes_per_sector.value * sectors_per_cluster.value
        self.sectors_per_cluster = sectors_per_cluster.value

    def read_clusters(self, cluster: int, clusters: int) -> bytes:
        """
        Read a number of clusters from the disk.

        :param int cluster: The starting cluster to read from.
        :param int clusters: The number of clusters to read.
        :return: The data read from the disk.
        :rtype: bytes
        :raises ValueError: If the number of clusters is less than or equal to 0.
        :raises ValueError: If the cluster is less than 0 or greater than the cluster count.
        :raises ValueError: If the number of sectors is less than or equal to 0.
        :raises ValueError: If the sector is less than 0 or greater than the sector count.
        :raises ValueError: If the buffer is too small to hold the data.
        :raises ctypes.WinError: If the read operation fails.
        """
        expected_length: int = self.cluster_size * clusters
        data: bytes = bytes(expected_length)
        sector: int = cluster * self.sectors_per_cluster
        sectors: int = clusters * self.sectors_per_cluster

        # Some sanity checks
        if clusters <= 0:
            raise ValueError("Number of clusters must be greater than 0")

        if cluster < 0 or cluster + clusters > self.cluster_count:
            raise ValueError("Invalid cluster range, out of bounds")

        if sectors <= 0:
            raise ValueError("Number of sectors must be greater than 0")

        if sector < 0 or sector + sectors > self.sector_count:
            raise ValueError("Invalid sector range, out of bounds")

        if len(data) < sectors * self.sector_size:
            raise ValueError("Buffer is too small to hold the data")

        # Calculate the offset in bytes
        offset_bytes: int = sector * self.sector_size

        # Move the current position to the offset
        if self.current_position != offset_bytes:
            # Move the current position to the offset
            if not SetFilePointer(self.handle, offset_bytes, None, 0):
                raise ctypes.WinError(ctypes.get_last_error())

            # Update the current position
            self.current_position = offset_bytes

        # Read the data from the disk
        bytes_read: wintypes.DWORD = wintypes.DWORD()

        if not ReadFile(self.handle, ctypes.byref(data), self.cluster_size * clusters, ctypes.byref(bytes_read), None):
            raise ctypes.WinError(ctypes.get_last_error())

        # Make sure length read is expected
        if bytes_read.value != expected_length:
            raise ValueError(f"Expected {expected_length} bytes, but got {bytes_read.value} bytes")

        return data

    def get_retrieval_pointers(self, file_handle: wintypes.HANDLE) -> list[FileExtent]:
        """
        Get the retrieval pointers for the disk.

        The retrieval pointers are used to find the location of the data on the disk.

        :param wintypes.HANDLE file_handle: The handle to the file to get the retrieval pointers for.
        :return: A list of file extents.
        :rtype: list[FileExtent]
        :raises ctypes.WinError: If the retrieval pointers cannot be obtained.
        """
        input_buffer: StartingVcnInputBuffer = StartingVcnInputBuffer(StartingVcn=0)
        input_size: int = ctypes.sizeof(input_buffer)
        chunk_size: int = 1024
        fsctl_get_ptrs: int = 0x00090073

        # Loop until we get the last error that isn't 234 (ERROR_MORE_DATA)
        while True:
            # Create a buffer to hold the retrieval pointers
            output_buffer: ctypes.Array[ctypes.c_char] = ctypes.create_string_buffer(chunk_size)
            bytes_returned: wintypes.DWORD = wintypes.DWORD(0)

            # Call DeviceIoControl to get the retrieval pointers.
            # We can check if it succeeds and then break out of the loop.
            if DeviceIoControl(
                file_handle,
                fsctl_get_ptrs,
                ctypes.byref(input_buffer),
                input_size,
                output_buffer,
                chunk_size,
                ctypes.byref(bytes_returned),
                None,
            ):
                break

            last_error: int = ctypes.get_last_error()

            # Increase the buffer size as we have more data
            if last_error == 234:  # ERROR_MORE_DATA
                output_buffer_size = max(output_buffer_size * 2, bytes_returned.value)
                continue

            raise ctypes.WinError(last_error)

        # Cast data to structure
        pointers: RetrievalPointersBuffer = ctypes.cast(output_buffer, ctypes.POINTER(RetrievalPointersBuffer)).contents
        extents: list[FileExtent] = []

        for i in range(pointers.ExtentCount):
            extent: RetrievalPointerExtent = ctypes.cast(
                ctypes.byref(pointers.Extents, i * ctypes.sizeof(RetrievalPointerExtent)),
                ctypes.POINTER(RetrievalPointerExtent),
            ).contents

            start_vcn: int = pointers.StartingVcn.value if i == 0 else pointers.Extents[i - 1].NextVcn.value

            extents.append(
                FileExtent(vcn=extent.NextVcn.value, lcn=extent.Lcn.value, size=extent.NextVcn.value - start_vcn)
            )

        return extents
