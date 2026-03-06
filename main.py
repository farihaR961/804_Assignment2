import os
import vtk

# -----------------------------
# 1) PATH TO DICOM FOLDER
# -----------------------------
DICOM_DIR = r"data\DicomTestImages"  

if not os.path.isdir(DICOM_DIR):
    raise FileNotFoundError(f"Folder not found: {DICOM_DIR}")

# quick check: confirm folder has files
files = os.listdir(DICOM_DIR)
if len(files) == 0:
    raise RuntimeError(f"No files found in: {DICOM_DIR}")

# -----------------------------
# 2) READ DICOM SERIES
# -----------------------------
reader = vtk.vtkDICOMImageReader()
reader.SetDirectoryName(DICOM_DIR)
reader.Update()

image = reader.GetOutput()

dims = image.GetDimensions()
spacing = image.GetSpacing()
minI, maxI = image.GetScalarRange()

# File size for report (sum of all DICOM files)
total_bytes = 0
for root, _, fnames in os.walk(DICOM_DIR):
    for f in fnames:
        fp = os.path.join(root, f)
        if os.path.isfile(fp):
            total_bytes += os.path.getsize(fp)

print("=== DATASET INFO (put in report) ===")
print("Dimensions:", dims)
print("Voxel resolution (spacing):", spacing)
print("Intensity range (min, max):", (minI, maxI))
print("Folder size (MB):", total_bytes / (1024 * 1024))

# -----------------------------
# 3) TRANSFER FUNCTIONS
# -----------------------------
colorTF = vtk.vtkColorTransferFunction()
opacityTF = vtk.vtkPiecewiseFunction()

colorTF.AddRGBPoint(minI, 0.0, 0.0, 0.0)
colorTF.AddRGBPoint(minI + 0.4*(maxI-minI), 1.0, 0.6, 0.4)
colorTF.AddRGBPoint(maxI, 1.0, 1.0, 1.0)

opacityTF.AddPoint(minI, 0.0)
opacityTF.AddPoint(minI + 0.35*(maxI-minI), 0.0)
opacityTF.AddPoint(minI + 0.70*(maxI-minI), 0.25)
opacityTF.AddPoint(maxI, 0.9)

# -----------------------------
# 4) VOLUME RENDERING
# -----------------------------
volMapper = vtk.vtkGPUVolumeRayCastMapper()
volMapper.SetInputData(image)

volProp = vtk.vtkVolumeProperty()
volProp.SetColor(colorTF)
volProp.SetScalarOpacity(opacityTF)
volProp.ShadeOn()
volProp.SetInterpolationTypeToLinear()

volume = vtk.vtkVolume()
volume.SetMapper(volMapper)
volume.SetProperty(volProp)

# -----------------------------
# 5) ISO-SURFACE (MARCHING CUBES)
# -----------------------------
isoValue = minI + 0.6*(maxI - minI)  # starting guess

mc = vtk.vtkMarchingCubes()
mc.SetInputData(image)
mc.SetValue(0, isoValue)
mc.Update()

surfMapper = vtk.vtkPolyDataMapper()
surfMapper.SetInputConnection(mc.GetOutputPort())
surfMapper.ScalarVisibilityOff()

surfActor = vtk.vtkActor()
surfActor.SetMapper(surfMapper)
surfActor.GetProperty().SetOpacity(1.0)

# -----------------------------
# 6) 3 VIEWPORTS
# -----------------------------
renWin = vtk.vtkRenderWindow()
renWin.SetSize(1500, 600)

ren1 = vtk.vtkRenderer()  # Volume
ren2 = vtk.vtkRenderer()  # Iso-surface
ren3 = vtk.vtkRenderer()  # Both

ren1.SetViewport(0.00, 0.0, 0.33, 1.0)
ren2.SetViewport(0.33, 0.0, 0.66, 1.0)
ren3.SetViewport(0.66, 0.0, 1.00, 1.0)

renWin.AddRenderer(ren1)
renWin.AddRenderer(ren2)
renWin.AddRenderer(ren3)

ren1.AddVolume(volume)
ren2.AddActor(surfActor)
ren3.AddVolume(volume)
ren3.AddActor(surfActor)

ren1.SetBackground(0.1, 0.1, 0.1)
ren2.SetBackground(0.1, 0.1, 0.1)
ren3.SetBackground(0.1, 0.1, 0.1)

# -----------------------------
# 7) SYNCHRONIZE CAMERA
# -----------------------------
cam = ren1.GetActiveCamera()
ren2.SetActiveCamera(cam)
ren3.SetActiveCamera(cam)
ren1.ResetCamera()

# -----------------------------
# 8) INTERACT
# -----------------------------
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

renWin.Render()
iren.Initialize()
iren.Start()
