import { Actions, Mutations } from 'vue-vtkjs-pvw-template/src/store/TYPES';

export default {
  state: {
    isovalue: 75,
  },
  getters: {
    VOLUME_ISOVALUE(state) {
      return state.isovalue;
    },
  },
  mutations: {
    VOLUME_ISOVALUE_SET(state, value) {
      state.isovalue = value;
    },
  },
  actions: {
    CONE_INITIALIZE({ rootState, dispatch }) {
      const client = rootState.network.client;
      if (client) {
        client
          .getRemote()
          .Cone.createVisualization()
          .then(
            ({ focalPoint, viewUp, position, centerOfRotation, bounds }) => {
              dispatch(Actions.VIEW_UPDATE_CAMERA, {
                focalPoint,
                viewUp,
                position,
                centerOfRotation,
                bounds,
              });
            }
          )
          .catch(console.error);
      }
    },
    VOLUME_UPDATE_ISOVALUE({ rootState, commit }, isovalue) {
      commit(Mutations.VOLUME_ISOVALUE_SET, isovalue);
      const client = rootState.network.client;
      if (client) {
        client.getRemote().Cone.updateIsovalue(isovalue);
      }
    },
    CONE_RESET_CAMERA({ rootState, dispatch }) {
      const client = rootState.network.client;
      if (client) {
        client
          .getRemote()
          .Cone.resetCamera()
          .then(
            ({ focalPoint, viewUp, position, centerOfRotation, bounds }) => {
              dispatch(Actions.VIEW_UPDATE_CAMERA, {
                focalPoint,
                viewUp,
                position,
                centerOfRotation,
                bounds,
              });
            }
          )
          .catch(console.error);
      }
    },
  },
};
