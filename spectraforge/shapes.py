"""
Geometric shapes for the ray tracer.

Each shape must implement the Hittable protocol with a `hit` method.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
import math

from .vec3 import Vec3, Point3
from .ray import Ray

if TYPE_CHECKING:
    from .materials import Material


@dataclass
class HitRecord:
    """Stores information about a ray-object intersection.

    Attributes:
        point: The intersection point in world space
        normal: The surface normal at the intersection (always points against ray)
        t: The ray parameter at intersection
        front_face: True if ray hit from outside the object
        material: The material at the hit point
        u, v: Texture coordinates at the hit point
    """
    point: Point3
    normal: Vec3
    t: float
    front_face: bool
    material: Optional[Material] = None
    u: float = 0.0
    v: float = 0.0

    def set_face_normal(self, ray: Ray, outward_normal: Vec3) -> None:
        """Set the normal to always point against the ray direction.

        Args:
            ray: The incoming ray
            outward_normal: The geometric normal pointing outward from surface
        """
        self.front_face = ray.direction.dot(outward_normal) < 0
        self.normal = outward_normal if self.front_face else -outward_normal


class Hittable(ABC):
    """Abstract base class for all objects that can be hit by rays."""

    @abstractmethod
    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        """Test if ray intersects this object.

        Args:
            ray: The ray to test
            t_min: Minimum t value to consider (avoid self-intersection)
            t_max: Maximum t value to consider

        Returns:
            HitRecord if intersection found, None otherwise
        """
        pass

    @abstractmethod
    def bounding_box(self) -> Optional['AABB']:
        """Get the axis-aligned bounding box for this object.

        Returns:
            AABB if the object is bounded, None otherwise
        """
        pass


class Sphere(Hittable):
    """A sphere defined by center and radius."""

    def __init__(self, center: Point3, radius: float, material: Optional[Material] = None):
        """Create a sphere.

        Args:
            center: Center point of the sphere
            radius: Radius of the sphere (can be negative for inward normals)
            material: Material for shading
        """
        self.center = center
        self.radius = radius
        self.material = material

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        """Test ray-sphere intersection using the quadratic formula.

        The equation (P-C)·(P-C) = r² where P = ray.at(t)
        expands to: t²(d·d) + 2t(d·(O-C)) + (O-C)·(O-C) - r² = 0
        which is the quadratic at² + bt + c = 0.
        """
        oc = ray.origin - self.center
        a = ray.direction.length_squared()
        half_b = oc.dot(ray.direction)
        c = oc.length_squared() - self.radius * self.radius

        discriminant = half_b * half_b - a * c
        if discriminant < 0:
            return None

        sqrtd = math.sqrt(discriminant)

        # Find the nearest root in the acceptable range
        root = (-half_b - sqrtd) / a
        if root < t_min or root > t_max:
            root = (-half_b + sqrtd) / a
            if root < t_min or root > t_max:
                return None

        point = ray.at(root)
        outward_normal = (point - self.center) / self.radius

        # Calculate UV coordinates for texturing
        u, v = self._get_sphere_uv(outward_normal)

        hit_record = HitRecord(
            point=point,
            normal=outward_normal,
            t=root,
            front_face=True,
            material=self.material,
            u=u,
            v=v
        )
        hit_record.set_face_normal(ray, outward_normal)

        return hit_record

    def _get_sphere_uv(self, point: Vec3) -> tuple[float, float]:
        """Get spherical UV coordinates for a point on the unit sphere.

        u: returned value [0,1] of angle around the Y axis from X=-1
        v: returned value [0,1] of angle from Y=-1 to Y=+1
        """
        theta = math.acos(-point.y)
        phi = math.atan2(-point.z, point.x) + math.pi

        u = phi / (2 * math.pi)
        v = theta / math.pi
        return u, v

    def bounding_box(self) -> Optional['AABB']:
        """Return the AABB containing this sphere."""
        r_vec = Vec3(abs(self.radius), abs(self.radius), abs(self.radius))
        return AABB(self.center - r_vec, self.center + r_vec)

    def __repr__(self) -> str:
        return f"Sphere(center={self.center}, radius={self.radius})"


class AABB:
    """Axis-Aligned Bounding Box for acceleration structures."""

    def __init__(self, minimum: Point3, maximum: Point3):
        """Create an AABB from corner points.

        Args:
            minimum: Corner with smallest x, y, z values
            maximum: Corner with largest x, y, z values
        """
        self.minimum = minimum
        self.maximum = maximum

    def hit(self, ray: Ray, t_min: float, t_max: float) -> bool:
        """Test if ray intersects this AABB using slab method.

        This uses Andrew Kensler's optimized algorithm.
        """
        for i in range(3):
            inv_d = 1.0 / ray.direction[i] if ray.direction[i] != 0 else float('inf')
            t0 = (self.minimum[i] - ray.origin[i]) * inv_d
            t1 = (self.maximum[i] - ray.origin[i]) * inv_d

            if inv_d < 0:
                t0, t1 = t1, t0

            t_min = max(t0, t_min)
            t_max = min(t1, t_max)

            if t_max <= t_min:
                return False

        return True

    @staticmethod
    def surrounding_box(box0: 'AABB', box1: 'AABB') -> 'AABB':
        """Return the AABB that contains both input boxes."""
        small = Point3(
            min(box0.minimum.x, box1.minimum.x),
            min(box0.minimum.y, box1.minimum.y),
            min(box0.minimum.z, box1.minimum.z)
        )
        big = Point3(
            max(box0.maximum.x, box1.maximum.x),
            max(box0.maximum.y, box1.maximum.y),
            max(box0.maximum.z, box1.maximum.z)
        )
        return AABB(small, big)

    def __repr__(self) -> str:
        return f"AABB(min={self.minimum}, max={self.maximum})"


class HittableList(Hittable):
    """A collection of hittable objects."""

    def __init__(self, objects: Optional[list[Hittable]] = None):
        self.objects: list[Hittable] = objects if objects is not None else []

    def add(self, obj: Hittable) -> None:
        """Add an object to the list."""
        self.objects.append(obj)

    def clear(self) -> None:
        """Remove all objects."""
        self.objects.clear()

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        """Find the closest intersection among all objects."""
        closest_hit: Optional[HitRecord] = None
        closest_t = t_max

        for obj in self.objects:
            hit_record = obj.hit(ray, t_min, closest_t)
            if hit_record is not None:
                closest_hit = hit_record
                closest_t = hit_record.t

        return closest_hit

    def bounding_box(self) -> Optional[AABB]:
        """Return the AABB containing all objects."""
        if not self.objects:
            return None

        first_box = True
        output_box: Optional[AABB] = None

        for obj in self.objects:
            box = obj.bounding_box()
            if box is None:
                return None

            if first_box:
                output_box = box
                first_box = False
            else:
                output_box = AABB.surrounding_box(output_box, box)

        return output_box

    def __len__(self) -> int:
        return len(self.objects)

    def __iter__(self):
        return iter(self.objects)


class Plane(Hittable):
    """An infinite plane defined by a point and normal."""

    def __init__(self, point: Point3, normal: Vec3, material: Optional[Material] = None):
        """Create a plane.

        Args:
            point: Any point on the plane
            normal: The plane's normal vector (will be normalized)
            material: Material for shading
        """
        self.point = point
        self.normal = normal.normalize()
        self.material = material

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        """Test ray-plane intersection."""
        denom = self.normal.dot(ray.direction)

        # Ray is parallel to plane
        if abs(denom) < 1e-8:
            return None

        t = (self.point - ray.origin).dot(self.normal) / denom

        if t < t_min or t > t_max:
            return None

        point = ray.at(t)

        # Simple planar UV mapping
        u = point.x - math.floor(point.x)
        v = point.z - math.floor(point.z)

        hit_record = HitRecord(
            point=point,
            normal=self.normal,
            t=t,
            front_face=True,
            material=self.material,
            u=u,
            v=v
        )
        hit_record.set_face_normal(ray, self.normal)

        return hit_record

    def bounding_box(self) -> Optional[AABB]:
        """Planes are infinite, so no bounding box."""
        return None


class Triangle(Hittable):
    """A triangle defined by three vertices."""

    def __init__(self, v0: Point3, v1: Point3, v2: Point3, material: Optional[Material] = None):
        """Create a triangle from three vertices.

        Args:
            v0, v1, v2: The three vertices in counter-clockwise order
            material: Material for shading
        """
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.material = material

        # Pre-compute edges and normal
        self.e1 = v1 - v0
        self.e2 = v2 - v0
        self.normal = self.e1.cross(self.e2).normalize()

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        """Test ray-triangle intersection using Möller-Trumbore algorithm."""
        h = ray.direction.cross(self.e2)
        a = self.e1.dot(h)

        # Ray is parallel to triangle
        if abs(a) < 1e-8:
            return None

        f = 1.0 / a
        s = ray.origin - self.v0
        u = f * s.dot(h)

        if u < 0.0 or u > 1.0:
            return None

        q = s.cross(self.e1)
        v = f * ray.direction.dot(q)

        if v < 0.0 or u + v > 1.0:
            return None

        t = f * self.e2.dot(q)

        if t < t_min or t > t_max:
            return None

        point = ray.at(t)
        hit_record = HitRecord(
            point=point,
            normal=self.normal,
            t=t,
            front_face=True,
            material=self.material,
            u=u,
            v=v
        )
        hit_record.set_face_normal(ray, self.normal)

        return hit_record

    def bounding_box(self) -> Optional[AABB]:
        """Return the AABB containing this triangle."""
        min_pt = Point3(
            min(self.v0.x, self.v1.x, self.v2.x) - 0.0001,
            min(self.v0.y, self.v1.y, self.v2.y) - 0.0001,
            min(self.v0.z, self.v1.z, self.v2.z) - 0.0001
        )
        max_pt = Point3(
            max(self.v0.x, self.v1.x, self.v2.x) + 0.0001,
            max(self.v0.y, self.v1.y, self.v2.y) + 0.0001,
            max(self.v0.z, self.v1.z, self.v2.z) + 0.0001
        )
        return AABB(min_pt, max_pt)
