import pytest
import drjit as dr
import mitsuba as mi

from .mesh_generation import create_stairs

from mitsuba.scalar_rgb.test.util import fresolver_append_path


def make_synthetic_scene(n_steps):
    props = mi.Properties("scene")
    props["_unnamed_0"] = create_stairs(n_steps)
    return mi.Scene(props)


def compare_results(res_a, res_b, atol=0.0):
    assert dr.all(res_a.is_valid() == res_b.is_valid())
    if dr.any(res_a.is_valid()):
        assert dr.allclose(res_a.t, res_b.t, atol=atol), "\n%s\n\n%s" % (res_a.t, res_b.t)


def test01_depth_scalar_stairs(variant_scalar_rgb):
    if mi.MI_ENABLE_EMBREE:
        pytest.skip("EMBREE enabled")

    n_steps = 20
    scene = make_synthetic_scene(n_steps)

    n = 128
    inv_n = 1.0 / (n-1)
    wavelengths = []

    for x in range(n - 1):
        for y in range(n - 1):
            o = [x * inv_n,  y * inv_n,  2]
            d = [0,  0,  -1]
            r = mi.Ray3f(o, d, 0.5, wavelengths)
            r.maxt = 100

            res_naive   = scene.ray_intersect_naive(r)
            res         = scene.ray_intersect(r)
            res_shadow  = scene.ray_test(r)

            step_idx = dr.floor((y * inv_n) * n_steps)

            assert dr.all(res_shadow)
            assert dr.all(res_shadow == res_naive.is_valid())
            expected = mi.SurfaceInteraction3f()
            expected.t = 2.0 - (step_idx / n_steps)
            compare_results(res_naive, expected, atol=1e-9)
            compare_results(res_naive, res)


@fresolver_append_path
def test02_depth_scalar_bunny(variant_scalar_rgb):
    if mi.MI_ENABLE_EMBREE:
        pytest.skip("EMBREE enabled")

    scene = mi.load_dict({
        "type" : "ply",
        "filename" : "resources/data/common/meshes/bunny_lowres.ply",
    })
    b = scene.bbox()

    n = 100
    inv_n = 1.0 / (n - 1)
    wavelengths = []

    for x in range(n):
        for y in range(n):
            o = [b.min[0] * (1 - x * inv_n) + b.max[0] * x * inv_n,
                 b.min[1] * (1 - y * inv_n) + b.max[1] * y * inv_n,
                 b.min[2]]
            d = [0, 0, 1]
            r = mi.Ray3f(o, d, 0.5, wavelengths)
            r.maxt = 100

            res_naive  = scene.ray_intersect_naive(r)
            res        = scene.ray_intersect(r)
            res_shadow = scene.ray_test(r)
            assert dr.all(res_shadow == res_naive.is_valid())
            compare_results(res_naive, res)
