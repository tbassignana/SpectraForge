"""
Light sources for the ray tracer.

Implements various light types:
- Point lights
- Area lights (rectangular)
- Directional lights (sun)
- Environment lights (HDR environment maps)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple
import math
import random

from .vec3 import Vec3, Point3, Color
from .ray import Ray
from .shapes import Hittable, HitRecord, Sphere, AABB
from .materials import Material, Emissive


@dataclass
class LightSample:
    """Result of sampling a light source."""
    direction: Vec3       # Direction from hit point to light
    distance: float       # Distance to the light
    intensity: Color      # Light intensity/color at this sample
    pdf: float           # Probability density of this sample


class Light(ABC):
    """Abstract base class for light sources."""

    @abstractmethod
    def sample(self, hit_point: Point3) -> LightSample:
        """Sample the light from a given point.

        Args:
            hit_point: The point we're illuminating

        Returns:
            LightSample with direction, distance, intensity, and pdf
        """
        pass

    @abstractmethod
    def power(self) -> float:
        """Return the total power of the light (for importance sampling)."""
        pass


class PointLight(Light):
    """A point light source.

    Point lights emit light equally in all directions from a single point.
    They produce hard shadows.
    """

    def __init__(self, position: Point3, color: Color, intensity: float = 1.0):
        """Create a point light.

        Args:
            position: Position of the light
            color: Color of the light
            intensity: Brightness multiplier
        """
        self.position = position
        self.color = color
        self.intensity = intensity

    def sample(self, hit_point: Point3) -> LightSample:
        direction = self.position - hit_point
        distance = direction.length()
        direction = direction.normalize()

        # Inverse square falloff
        attenuation = 1.0 / (distance * distance)
        light_intensity = self.color * self.intensity * attenuation

        return LightSample(
            direction=direction,
            distance=distance,
            intensity=light_intensity,
            pdf=1.0  # Delta light, no sampling
        )

    def power(self) -> float:
        return self.intensity * (self.color.r + self.color.g + self.color.b) / 3.0


class DirectionalLight(Light):
    """A directional light (like the sun).

    Directional lights have parallel rays and no falloff.
    """

    def __init__(self, direction: Vec3, color: Color, intensity: float = 1.0):
        """Create a directional light.

        Args:
            direction: Direction the light is coming FROM
            color: Color of the light
            intensity: Brightness multiplier
        """
        self.direction = direction.normalize()
        self.color = color
        self.intensity = intensity

    def sample(self, hit_point: Point3) -> LightSample:
        return LightSample(
            direction=-self.direction,  # Direction TO the light
            distance=float('inf'),      # Infinitely far
            intensity=self.color * self.intensity,
            pdf=1.0
        )

    def power(self) -> float:
        return self.intensity * (self.color.r + self.color.g + self.color.b) / 3.0


class AreaLight(Light, Hittable):
    """A rectangular area light.

    Area lights produce soft shadows and are physically plausible.
    The light emits from a rectangle defined by a corner and two edge vectors.
    """

    def __init__(
        self,
        corner: Point3,
        edge1: Vec3,
        edge2: Vec3,
        color: Color,
        intensity: float = 1.0
    ):
        """Create a rectangular area light.

        Args:
            corner: One corner of the rectangle
            edge1: Vector along one edge
            edge2: Vector along the other edge (should be perpendicular)
            color: Color of the light
            intensity: Brightness multiplier
        """
        self.corner = corner
        self.edge1 = edge1
        self.edge2 = edge2
        self.color = color
        self.intensity = intensity

        # Compute normal and area
        self.normal = edge1.cross(edge2).normalize()
        self.area = edge1.cross(edge2).length()

        # Create emissive material for the light
        self.material = Emissive(color, intensity)

    def sample(self, hit_point: Point3) -> LightSample:
        """Sample a random point on the area light."""
        # Random point on the rectangle
        u = random.random()
        v = random.random()
        light_point = self.corner + self.edge1 * u + self.edge2 * v

        direction = light_point - hit_point
        distance = direction.length()
        direction = direction.normalize()

        # Check if we're on the right side of the light
        cos_angle = -direction.dot(self.normal)
        if cos_angle <= 0:
            return LightSample(
                direction=direction,
                distance=distance,
                intensity=Color(0, 0, 0),
                pdf=1.0
            )

        # PDF for uniform sampling on rectangle
        # Convert from area pdf to solid angle pdf
        pdf = (distance * distance) / (cos_angle * self.area)

        light_intensity = self.color * self.intensity

        return LightSample(
            direction=direction,
            distance=distance,
            intensity=light_intensity,
            pdf=pdf
        )

    def power(self) -> float:
        return self.area * self.intensity * (self.color.r + self.color.g + self.color.b) / 3.0

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        """Test ray intersection with the area light rectangle."""
        # Check if ray is parallel to plane
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None

        # Find intersection with plane
        t = (self.corner - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None

        # Check if point is inside rectangle
        point = ray.at(t)
        local = point - self.corner

        # Project onto edges
        u = local.dot(self.edge1.normalize()) / self.edge1.length()
        v = local.dot(self.edge2.normalize()) / self.edge2.length()

        if u < 0 or u > 1 or v < 0 or v > 1:
            return None

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
        """Return the AABB for this area light."""
        p0 = self.corner
        p1 = self.corner + self.edge1
        p2 = self.corner + self.edge2
        p3 = self.corner + self.edge1 + self.edge2

        min_pt = Point3(
            min(p0.x, p1.x, p2.x, p3.x) - 0.001,
            min(p0.y, p1.y, p2.y, p3.y) - 0.001,
            min(p0.z, p1.z, p2.z, p3.z) - 0.001
        )
        max_pt = Point3(
            max(p0.x, p1.x, p2.x, p3.x) + 0.001,
            max(p0.y, p1.y, p2.y, p3.y) + 0.001,
            max(p0.z, p1.z, p2.z, p3.z) + 0.001
        )

        return AABB(min_pt, max_pt)


class SphereLight(Light, Hittable):
    """A spherical area light.

    Useful for representing spherical light sources like light bulbs.
    """

    def __init__(
        self,
        center: Point3,
        radius: float,
        color: Color,
        intensity: float = 1.0
    ):
        """Create a spherical light.

        Args:
            center: Center of the sphere
            radius: Radius of the sphere
            color: Color of the light
            intensity: Brightness multiplier
        """
        self.center = center
        self.radius = radius
        self.color = color
        self.intensity = intensity

        # Create the underlying sphere with emissive material
        self.material = Emissive(color, intensity)
        self._sphere = Sphere(center, radius, self.material)

    def sample(self, hit_point: Point3) -> LightSample:
        """Sample a point on the visible hemisphere of the sphere."""
        direction = self.center - hit_point
        distance_to_center = direction.length()

        if distance_to_center < self.radius:
            # We're inside the sphere - special case
            random_dir = Vec3.random_unit_vector()
            return LightSample(
                direction=random_dir,
                distance=self.radius,
                intensity=self.color * self.intensity,
                pdf=1.0 / (4 * math.pi)
            )

        # Sample a direction towards the sphere
        direction = direction.normalize()

        # Create an orthonormal basis
        up = Vec3(0, 1, 0) if abs(direction.y) < 0.999 else Vec3(1, 0, 0)
        tangent = up.cross(direction).normalize()
        bitangent = direction.cross(tangent)

        # Compute the solid angle subtended by the sphere
        sin_theta_max = self.radius / distance_to_center
        cos_theta_max = math.sqrt(max(0, 1 - sin_theta_max * sin_theta_max))

        # Sample uniformly within the cone
        u = random.random()
        v = random.random()

        cos_theta = 1 - u * (1 - cos_theta_max)
        sin_theta = math.sqrt(1 - cos_theta * cos_theta)
        phi = 2 * math.pi * v

        # Convert to direction
        sample_dir = (
            tangent * (sin_theta * math.cos(phi)) +
            bitangent * (sin_theta * math.sin(phi)) +
            direction * cos_theta
        ).normalize()

        # Intersect with sphere to get actual distance
        # Use simplified formula since we're sampling towards sphere
        proj = (self.center - hit_point).dot(sample_dir)
        d_sq = (self.center - hit_point).length_squared() - proj * proj
        thc = math.sqrt(max(0, self.radius * self.radius - d_sq))
        distance = proj - thc

        if distance < 0:
            distance = proj + thc

        # PDF for cone sampling
        pdf = 1.0 / (2 * math.pi * (1 - cos_theta_max))

        return LightSample(
            direction=sample_dir,
            distance=distance,
            intensity=self.color * self.intensity,
            pdf=pdf
        )

    def power(self) -> float:
        return 4 * math.pi * self.radius * self.radius * self.intensity * \
               (self.color.r + self.color.g + self.color.b) / 3.0

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        """Delegate to internal sphere."""
        return self._sphere.hit(ray, t_min, t_max)

    def bounding_box(self) -> Optional[AABB]:
        """Delegate to internal sphere."""
        return self._sphere.bounding_box()


class LightList:
    """Collection of lights for sampling."""

    def __init__(self, lights: list[Light] = None):
        self.lights: list[Light] = lights if lights else []
        self._total_power: float = 0.0
        self._update_power()

    def add(self, light: Light) -> None:
        """Add a light to the list."""
        self.lights.append(light)
        self._update_power()

    def _update_power(self) -> None:
        """Update total power for importance sampling."""
        self._total_power = sum(l.power() for l in self.lights)

    def sample(self, hit_point: Point3) -> Tuple[LightSample, int]:
        """Sample a light using power-based importance sampling.

        Returns:
            Tuple of (LightSample, light_index)
        """
        if not self.lights:
            return LightSample(Vec3(0, 0, 0), 0, Color(0, 0, 0), 1.0), -1

        if len(self.lights) == 1:
            return self.lights[0].sample(hit_point), 0

        # Power-weighted random selection
        r = random.random() * self._total_power
        cumulative = 0.0
        selected_idx = len(self.lights) - 1

        for i, light in enumerate(self.lights):
            cumulative += light.power()
            if r <= cumulative:
                selected_idx = i
                break

        light_sample = self.lights[selected_idx].sample(hit_point)

        # Adjust PDF for light selection probability
        selection_pdf = self.lights[selected_idx].power() / self._total_power
        light_sample.pdf *= selection_pdf

        return light_sample, selected_idx

    def __len__(self) -> int:
        return len(self.lights)

    def __iter__(self):
        return iter(self.lights)
