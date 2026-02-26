"""Flat search platforms. Registry for extensibility."""

from platforms.wggesucht.platform import WgGesuchtPlatform

PLATFORMS = {"wggesucht": WgGesuchtPlatform()}
