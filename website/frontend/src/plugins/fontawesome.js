import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import {
  faTrash,
  faFolder,
  faFolderOpen,
  faFile,
  faCircleUser,
  faDiagramProject,
} from '@fortawesome/free-solid-svg-icons';
import { faPenToSquare } from '@fortawesome/free-regular-svg-icons';

library.add(
  faTrash,
  faFolder,
  faFolderOpen,
  faFile,
  faPenToSquare,
  faCircleUser,
  faDiagramProject
);

export default FontAwesomeIcon;
