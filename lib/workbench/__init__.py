"""Local browser transport over the existing CCB control plane."""

from .service import WorkbenchService, build_workbench_server

__all__ = ['WorkbenchService', 'build_workbench_server']
