import { Reducer } from 'redux';

import { actionTypes, OutputsAction } from '../actions/outputs';
import { OutputsEmptyState, OutputsModel, OutputsNode } from '../models/outputs';

export const outputsReducer: Reducer<OutputsModel> =
  (state: OutputsModel = OutputsEmptyState, action: OutputsAction) => {
    switch (action.type) {

      case actionTypes.RECEIVE_OUTPUTS_FILE:
        const newFiles: { [key: string]: string } = {};
        newFiles[action.path] = action.outputsFile;
        return {
          ...state,
          outputsFiles: {...state.outputsFiles, ...newFiles}
        };
      case actionTypes.RECEIVE_OUTPUTS_TREE:
        let outputsNode: OutputsNode;
        let outputsFiles: { [key: string]: string };
        if (!action.path) {
          outputsNode = new OutputsNode(true, '', true, '', {});
          outputsFiles = {};
          outputsNode.setChildren(action.path, action.outputsTree.files, action.outputsTree.dirs);
        } else {
          outputsNode = state.outputsTree.root.deepCopy();
          outputsFiles = state.outputsFiles;
        }
        if (action.path) {
          const node = OutputsNode.findChild(outputsNode, action.path);
          node.setChildren(action.path, action.outputsTree.files, action.outputsTree.dirs);
        }

        return {
          ...state,
          outputsTree: {root : outputsNode},
          outputsFiles
        };
      default:
        return state;
    }
  };
