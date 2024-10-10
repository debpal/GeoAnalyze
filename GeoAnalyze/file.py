import os
import shutil


class File:

    '''
    Functionality for file operations.
    '''

    def delete_by_name(
        self,
        folder_path: str,
        file_names: list[str]
    ) -> str:

        '''
        Delete files of the same name irrespective of extensions and
        return a list o deleted file names.

        Parameters
        ----------
        folder_path : str
            Path of the input folder.

        file_names : list
            List of file names (without extension) to delete.

        Returns
        -------
        str
            File names that were deleted.
        '''

        folder_contents = map(
            lambda x: os.path.join(folder_path, x), os.listdir(folder_path)
        )

        file_paths = filter(
            lambda x: os.path.isfile(x), folder_contents
        )

        delete_paths = filter(
            lambda x: os.path.split(x)[-1].split('.')[0] in file_names, file_paths
        )

        delete_files = list(
            map(
                lambda x: os.path.split(x)[-1], delete_paths
            )
        )

        for i in delete_files:
            os.remove(
                os.path.join(folder_path, i)
            )

        output = f'List of deleted files: {delete_files}.'

        return output

    def transfer_by_name(
        self,
        src_folder: str,
        dst_folder: str,
        file_names: list[str]
    ) -> str:

        '''
        Transfer files of the same name irrespective of extensions from
        the source folder to the destination folder.

        Parameters
        ----------
        src_folder : str
            Path of the source folder.

        dst_folder : str
            Path of the destination folder.

        file_names : list
            List of file names (without extension) to transfer.

        Returns
        -------
        str
            File names that were transferred.
        '''

        src_contents = map(
            lambda x: os.path.join(src_folder, x), os.listdir(src_folder)
        )

        src_paths = filter(
            lambda x: os.path.isfile(x), src_contents
        )

        transfer_paths = filter(
            lambda x: os.path.split(x)[-1].split('.')[0] in file_names, src_paths
        )

        transfer_files = list(
            map(
                lambda x: os.path.split(x)[-1], transfer_paths
            )
        )

        for i in transfer_files:
            shutil.copy2(
                os.path.join(src_folder, i), os.path.join(dst_folder, i)
            )

        output = f'List of transferred files: {transfer_files}.'

        return output
