import os


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
