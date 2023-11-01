import itk
import numpy as np


def run_registration(
    fixed_image,
    moving_image,
    rigid=True,
    affine=True,
    bspline=True,
    affine_iterations="2048",
    log=False,
):
    # convert to ITK, view only
    fixed_image = itk.GetImageViewFromArray(fixed_image).astype(itk.F)
    moving_image = itk.GetImageViewFromArray(moving_image).astype(itk.F)

    # This syntax needed for 3D images
    elastix_object = itk.ElastixRegistrationMethod.New(
        fixed_image, moving_image
    )

    parameter_object = setup_parameter_object(
        rigid=rigid,
        affine=affine,
        bspline=bspline,
        affine_iterations=affine_iterations,
    )
    elastix_object.SetParameterObject(parameter_object)
    elastix_object.SetLogToConsole(log)

    # update filter object
    elastix_object.UpdateLargestPossibleRegion()

    # get results
    result_image = elastix_object.GetOutput()
    result_transform_parameters = elastix_object.GetTransformParameterObject()
    return np.asarray(result_image), result_transform_parameters


def setup_parameter_object(
    rigid=True,
    affine=True,
    bspline=True,
    affine_iterations="2048",
):
    parameter_object = itk.ParameterObject.New()

    if rigid:
        parameter_map_rigid = parameter_object.GetDefaultParameterMap("rigid")
        parameter_object.AddParameterMap(parameter_map_rigid)

    if affine:
        parameter_map_affine = parameter_object.GetDefaultParameterMap(
            "affine"
        )
        parameter_map_affine["MaximumNumberOfIterations"] = [affine_iterations]
        parameter_object.AddParameterMap(parameter_map_affine)

    if bspline:
        parameter_map_bspline = parameter_object.GetDefaultParameterMap(
            "bspline"
        )
        parameter_object.AddParameterMap(parameter_map_bspline)

    return parameter_object
