"""
SpectraForge - A Python Ray Tracing Renderer

A complete, optimized ray tracing renderer with support for:
- Global illumination (path tracing)
- Subsurface scattering
- Volumetric effects
- PBR materials (GGX/Cook-Torrance)
- Multi-threaded acceleration structures (BVH)
- HDR image output
- Cross-platform support (ARM/x86)
"""

__version__ = "0.1.0"
__author__ = "SpectraForge Team"

from .vec3 import Vec3, Point3, Color
from .ray import Ray
from .shapes import Sphere, Plane, Triangle, HittableList, AABB, HitRecord, Hittable
from .materials import Material, Lambertian, Metal, Dielectric, Emissive, PBRMaterial
from .camera import Camera
from .renderer import Renderer, RenderSettings, get_platform_info
from .bvh import BVH, BVHNode, build_bvh
from .lights import Light, PointLight, DirectionalLight, AreaLight, SphereLight, LightList
from .volumes import ConstantMedium, SubsurfaceScatteringMaterial, create_fog, create_smoke
from .scene_parser import SceneParser, load_scene, parse_scene
