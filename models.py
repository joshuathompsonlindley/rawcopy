import ctypes
from ctypes import wintypes
from dataclasses import dataclass


# DISK_GEOMETRY - https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-disk_geometry
class DiskGeometry(ctypes.Structure):
    _fields_ = [
        ("Cylinders", wintypes.ULARGE_INTEGER),
        ("MediaType", wintypes.DWORD),
        ("TracksPerCylinder", wintypes.DWORD),
        ("SectorsPerTrack", wintypes.DWORD),
        ("BytesPerSector", wintypes.DWORD),
    ]

    disk_size = property(
        lambda self: self.Cylinders * self.TracksPerCylinder * self.SectorsPerTrack * self.BytesPerSector
    )


# GET_LENGTH_INFORMATION - https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-get_length_information
class GetLengthInformation(ctypes.Structure):
    _fields_ = [("Length", wintypes.ULARGE_INTEGER)]


# STARTING_VCN_INPUT_BUFFER - https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-starting_vcn_input_buffer
class StartingVcnInputBuffer(ctypes.Structure):
    _fields_ = [("StartingVcn", wintypes.ULARGE_INTEGER)]


class RetrievalPointerExtent(ctypes.Structure):
    _fields_ = [
        ("NextVcn", wintypes.ULARGE_INTEGER),
        ("Lcn", wintypes.ULARGE_INTEGER),
    ]


# RETRIEVAL_POINTERS_BUFFER - https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-retrieval_pointers_buffer
class RetrievalPointersBuffer(ctypes.Structure):
    _fields_ = [
        ("ExtentCount", wintypes.DWORD),
        ("StartingVcn", wintypes.ULARGE_INTEGER),
        ("Extents", RetrievalPointerExtent * 1),
        # The number of extents is not known at compile time, so we use a flexible array member
    ]


@dataclass
class FileExtent:
    vcn: int
    lcn: int
    size: int
