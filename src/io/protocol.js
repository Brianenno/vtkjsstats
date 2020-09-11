/* eslint-disable arrow-body-style */
export default function createMethods(session) {
  return {
    createVisualization: () => session.call('vtk.initialize', []),
    resetCamera: () => session.call('vtk.camera.reset', []),
    updateIsovalue: (isovalue) =>
      session.call('vtk.volume.isovalue.update', [isovalue]),
  };
}
