import ctypes
from ctypes import wintypes

# CreateFileW - https://learn.microsoft.com/en-us/windows/win32/api/file/nf-file-createfilew
# Arguments: lpFileName, dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile
# Return: HANDLE
CreateFile = ctypes.windll.kernel32.CreateFileW
CreateFile.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
CreateFile.restype = wintypes.HANDLE

# GetFreeDiskSpaceA - https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getdiskfreespaceA
# Arguments: lpRootPathName, lpSectorsPerCluster, lpBytesPerSector, lpNumberOfFreeClusters, lpTotalNumberOfClusters
# Return: BOOL
GetFreeDiskSpace = ctypes.windll.kernel32.GetDiskFreeSpaceA
GetFreeDiskSpace.argtypes = [
    wintypes.LPCWSTR,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
]
GetFreeDiskSpace.restype = wintypes.BOOL


# DeviceIoControl - https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-deviceiocontrol
# Arguments: hDevice, dwIoControlCode, lpInBuffer, nInBufferSize, lpOutBuffer, nOutBufferSize, lpBytesReturned, lpOverlapped
# Return: BOOL
DeviceIoControl = ctypes.windll.kernel32.DeviceIoControl
DeviceIoControl.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p,
]
DeviceIoControl.restype = wintypes.BOOL

# CloseHandle - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-closehandle
# Arguments: hObject
# Return: BOOL
CloseHandle = ctypes.windll.kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

# SetFilePointer - https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfilepointer
# Arguments: hFile, lDistanceToMove, lpDistanceToMoveHigh, dwMoveMethod
# Return: DWORD
SetFilePointer = ctypes.windll.kernel32.SetFilePointer
SetFilePointer.argtypes = [
    wintypes.HANDLE,
    ctypes.c_long,
    ctypes.POINTER(ctypes.c_long),
    wintypes.DWORD,
]
SetFilePointer.restype = wintypes.DWORD


# ReadFile - https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile
# Arguments: hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped
# Return: BOOL
ReadFile = ctypes.windll.kernel32.ReadFile
ReadFile.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p,
]
ReadFile.restype = wintypes.BOOL
