import time

from vtk.web import protocols as vtk_protocols

from wslink import register as exportRpc

# import Twisted reactor for later callback
from twisted.internet import reactor

import vtk

# -------------------------------------------------------------------------
# ViewManager
# -------------------------------------------------------------------------

class VtkVolume(vtk_protocols.vtkWebProtocol):
    def __init__(self):
        self.volume = vtk.vtkVolume()

    def getCamera(self):
        renderWindow = self.getView('-1')
        rr = renderWindow.GetRenderers().GetFirstRenderer()
        bounds = rr.ComputeVisiblePropBounds()
        camera = rr.GetActiveCamera()

        return {
          'id': self.getGlobalId(renderWindow),
          'bounds': bounds,
          'position': tuple(camera.GetPosition()),
          'viewUp': tuple(camera.GetViewUp()),
          'focalPoint': tuple(camera.GetFocalPoint()),
          'centerOfRotation': (0, 0, 0),
        }

    alreadyCall = False

    @exportRpc("vtk.initialize")
    def createVisualization(self):

        if self.alreadyCall:
          return

        self.alreadyCall = True

        global renderer, renderWindow, renderWindowInteractor, reader, reader_Bones, reader_Blood, reader_Skin, isovalue, BonesMapper, BonesActor, BloodActor, BloodMapper, SkinActor, SkinMapper, volume, volumeMapper, ClippingPlane, ImagePlane, iss, ctf

        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        # Read the volumetric image
        filename_vol = "CT.vtk"
        reader = vtk.vtkStructuredPointsReader()
        reader.SetFileName(filename_vol)
        reader.Update()
        # Read the meshes
        filename_mesh = "Bones.obj"
        reader_Bones = vtk.vtkOBJReader()
        reader_Bones.SetFileName(filename_mesh)
        reader_Bones.Update()
        filename_mesh = "Skin.obj"
        reader_Skin = vtk.vtkOBJReader()
        reader_Skin.SetFileName(filename_mesh)
        reader_Skin.Update()
        filename_mesh = "Blood.obj"
        reader_Blood = vtk.vtkOBJReader()
        reader_Blood.SetFileName(filename_mesh)
        reader_Blood.Update()
        # Shift and scale input data between 0 and 255
        range = 255
        a,b = reader.GetOutput().GetScalarRange()
        iss = vtk.vtkImageShiftScale()
        iss.SetInputData(reader.GetOutput())
        iss.SetShift(-a)
        iss.SetScale(range/(b-a))
        iss.SetOutputScalarTypeToUnsignedChar()            
        # Volume mapper
        volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
        volumeMapper.SetInputConnection(iss.GetOutputPort()) 
        volumeMapper.SetBlendModeToIsoSurface()
        ####################### COLOR FUNCTION ####################### 
        colorTransferFunction = vtk.vtkColorTransferFunction()
        #Background
        colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
        #Lungs
        colorTransferFunction.AddRGBPoint(30.0, 0.9059, 0.6314, 0.6902)
        colorTransferFunction.AddRGBPoint(40.0, 0.9059, 0.6314, 0.6902)
        #General Tissue
        colorTransferFunction.AddRGBPoint(50, 1.0 , 1.0 , 0.0)
        colorTransferFunction.AddRGBPoint(60, 1.0 , 1.0 , 0.0)
        #Cardiac Tissue  1.0000    0.3882    0.2784
        colorTransferFunction.AddRGBPoint(61.0, 1.0 , 0.3882, 0.2784)
        colorTransferFunction.AddRGBPoint(75.0, 1.0 , 0.3882, 0.2784)
        #Blood
        colorTransferFunction.AddRGBPoint(85,1.0 , 0.0, 0.0)
        colorTransferFunction.AddRGBPoint(105,1.0 , 0.0, 0.0)
        #Bones
        colorTransferFunction.AddRGBPoint(110,1.0 , 1.0, 1.0)
        ####################### OPACITY FUNCTION ####################### 
        opacityTransferFunction_ct = vtk.vtkPiecewiseFunction();
        #Background
        opacityTransferFunction_ct.AddPoint(25.0, 0.0)
        #Lungs
        opacityTransferFunction_ct.AddPoint(30.0, 0.0)
        opacityTransferFunction_ct.AddPoint(40.0, 0.0)
        opacityTransferFunction_ct.AddPoint(40.1, 0.1)
        #General Tissue
        opacityTransferFunction_ct.AddPoint(50.0, 0.05)
        opacityTransferFunction_ct.AddPoint(64.0, 0.05)
        # Cardiac Tissue
        opacityTransferFunction_ct.AddPoint(65.0, 1)
        opacityTransferFunction_ct.AddPoint(75.0, 1)
        # Blood
        opacityTransferFunction_ct.AddPoint(85.0, 0.03)
        opacityTransferFunction_ct.AddPoint(100.0, 0.03)
        #Bones
        opacityTransferFunction_ct.AddPoint(110.0, 0.5)
        ####################### GRADIENT FUNCTION ####################### 
        val_grad = 0
        gradient_function_ct = vtk.vtkPiecewiseFunction();
        gradient_function_ct.AddPoint(val_grad, 1.0)
        ####################### VOLUME  ####################### 
        #Properties
        isovalue = 75.0
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.GetIsoSurfaceValues().SetValue(0, isovalue)
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(opacityTransferFunction_ct)
        volumeProperty.SetGradientOpacity(gradient_function_ct) 
        volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()
        #Volume
        volume = self.volume
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        volume.VisibilityOn()
        # Mesh Mappers and actors
        BonesMapper = vtk.vtkPolyDataMapper()
        BonesActor = vtk.vtkActor()
        BonesMapper.SetInputConnection(reader_Bones.GetOutputPort())
        BonesActor.SetMapper(BonesMapper)
        BonesActor.GetProperty().SetColor(0.93, 0.92, 0.756)
        BonesActor.GetProperty().SetOpacity(0.9)
        BloodMapper = vtk.vtkPolyDataMapper()
        BloodActor = vtk.vtkActor()
        BloodMapper.SetInputConnection(reader_Blood.GetOutputPort())
        BloodActor.SetMapper(BloodMapper)
        BloodActor.GetProperty().SetColor(1.0, 0, 0)
        SkinMapper = vtk.vtkPolyDataMapper()
        SkinActor = vtk.vtkActor()
        SkinMapper.SetInputConnection(reader_Skin.GetOutputPort())
        SkinActor.SetMapper(SkinMapper)
        SkinActor.GetProperty().SetColor(1.0, 0.8, 0.8)
        SkinActor.GetProperty().SetOpacity(0.6)
        # Renderer & renderWindow
        renderer.AddVolume(volume)
        renderer.AddActor(BonesActor)
        renderer.AddActor(SkinActor)
        renderer.AddActor(BloodActor)
        # Clipping ImagePlane 
        ClippingPlane = vtk.vtkPlane()
        ClippingPlane.SetNormal([1.0, 0.0, 0.0])
        xmin,xmax,ymin,ymax,zmin,zmax = volume.GetBounds()
        ClippingPlane.SetOrigin((xmin+xmax)/2,(ymin+ymax)/2,(zmin+zmax)/2)
        volumeMapper.AddClippingPlane(ClippingPlane)
        volume.Update()
        # Outline
        outlineData = vtk.vtkOutlineFilter()
        outlineData.SetInputConnection(reader.GetOutputPort())
        mapOutline = vtk.vtkPolyDataMapper()
        mapOutline.SetInputConnection(outlineData.GetOutputPort())
        outline = vtk.vtkActor()
        outline.SetMapper(mapOutline)
        outline.GetProperty().SetColor(1.0, 1.0, 0.0)
        renderer.AddActor(outline)
        # Cutter
        BonesMapper.AddClippingPlane(ClippingPlane)
        SkinMapper.AddClippingPlane(ClippingPlane)
        BloodMapper.AddClippingPlane(ClippingPlane)
        ####################### CREATE PLANES ####################### 
        # Grayscale Colormap
        ctf = vtk.vtkLookupTable()
        ctf.SetTableRange(0,1)
        ctf.SetHueRange(1.0,1.0)
        ctf.SetSaturationRange(0.0,0.0)
        ctf.SetValueRange(0,1)
        ctf.Build()
        # Window Interactor
        renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renderWindow)
        renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        renderWindowInteractor.EnableRenderOff()
        # ImagePlane 
        ImagePlane = vtk.vtkImagePlaneWidget()
        ImagePlane.SetInputConnection(iss.GetOutputPort())
        ImagePlane.SetPlaneOrientationToXAxes()
        ImagePlane.SetLookupTable(ctf)
        ImagePlane.SetSlicePosition(int((ymax+ymin)/2))
        # ImagePlane.SetPicker(picker)
        ImagePlane.DisplayTextOn()
        ImagePlane.SetInteractor(renderWindowInteractor)
        ImagePlane.EnabledOn()
        ImagePlane.SetLeftButtonAction(1)
        ImagePlane.SetMiddleButtonAction(0)
        def ImagePlaneScript(obj,event):
            ClipPlaneOrigin = tuple(map(sum, zip(obj.GetOrigin(), tuple(-i for i in obj.GetNormal()))))
            ClippingPlane.SetOrigin(ClipPlaneOrigin)
            ClippingPlane.SetNormal(obj.GetNormal())
        ImagePlane.AddObserver('InteractionEvent',ImagePlaneScript)
        ImagePlane.InteractionOn()
        # Renderer & render window
        renderer.ResetCamera()
        renderWindow.Render()

        return self.resetCamera()


    @exportRpc("vtk.camera.reset")
    def resetCamera(self):
        renderWindow = self.getView('-1')
        renderWindow.GetRenderers().GetFirstRenderer().ResetCamera()
        renderWindow.Render()

        self.getApplication().InvalidateCache(renderWindow)
        self.getApplication().InvokeEvent('UpdateEvent')

        return self.getCamera()


    # @exportRpc("vtk.cone.resolution.update")
    # def updateResolution(self, resolution):
        # self.cone.SetResolution(resolution)
        # renderWindow = self.getView('-1')
        # renderWindow.Render()
        # self.getApplication().InvokeEvent('UpdateEvent')
    
    
    @exportRpc("vtk.volume.isovalue.update")
    def updateIsovalue(self, isovalue):
        self.volume.GetProperty().GetIsoSurfaceValues().SetValue(0, isovalue)
        renderWindow = self.getView('-1')
        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')


    @exportRpc("viewport.mouse.zoom.wheel")
    def updateZoomFromWheel(self, event):
      if 'Start' in event["type"]:
        self.getApplication().InvokeEvent('StartInteractionEvent')

      renderWindow = self.getView(event['view'])
      if renderWindow and 'spinY' in event:
        zoomFactor = 1.0 - event['spinY'] / 10.0

        camera = renderWindow.GetRenderers().GetFirstRenderer().GetActiveCamera()
        fp = camera.GetFocalPoint()
        pos = camera.GetPosition()
        delta = [fp[i] - pos[i] for i in range(3)]
        camera.Zoom(zoomFactor)

        pos2 = camera.GetPosition()
        camera.SetFocalPoint([pos2[i] + delta[i] for i in range(3)])
        renderWindow.Modified()

      if 'End' in event["type"]:
        self.getApplication().InvokeEvent('EndInteractionEvent')
      
