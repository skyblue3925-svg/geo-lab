import { normalizeStudentLayer } from "../domain/student-layer.js";
import { normalizeImportedPublicLayer } from "../public-layer-imports.js";

function normalizeStringArray(values) {
  return Array.isArray(values)
    ? values
        .map((value) => String(value ?? "").trim())
        .filter(Boolean)
    : [];
}

function normalizeLocalPublicVisibility(rawVisibility, localPublicLayers) {
  return Object.fromEntries(
    localPublicLayers.map((layer) => [layer.id, Boolean(rawVisibility?.[layer.id])]),
  );
}

function normalizeLocalPublicOpacity(rawOpacity, localPublicLayers) {
  return Object.fromEntries(
    localPublicLayers.map((layer) => {
      const value = Number(rawOpacity?.[layer.id]);
      return [layer.id, Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 1];
    }),
  );
}

function formatSavedAt(savedAt) {
  const date = new Date(savedAt);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function buildWorkspaceProjectSnapshot({
  idFactory,
  name,
  workspaceValues,
  viewMode,
  baseMapMode,
  mapOverlayLayerIds,
  showSchoolReference,
  localPublicVisibility,
  localPublicOpacity,
  importedPublicLayers,
  studentLayers,
  reflectionNote,
  sgisControls,
  activeLayerId,
  existingProjectId = null,
}) {
  const trimmedName = String(name ?? "").trim();
  if (!trimmedName) {
    throw new Error("프로젝트 이름을 먼저 입력해 주세요.");
  }

  return {
    id: existingProjectId || idFactory("workspace-project"),
    name: trimmedName,
    savedAt: new Date().toISOString(),
    viewMode: viewMode === "korea" ? "korea" : "school",
    baseMapMode: String(baseMapMode ?? "roadmap"),
    mapOverlayLayerIds: normalizeStringArray(mapOverlayLayerIds),
    showSchoolReference: showSchoolReference !== false,
    workspaceValues: {
      schoolName: workspaceValues.schoolName,
      lat: Number(workspaceValues.lat),
      lng: Number(workspaceValues.lng),
      radiusMeters: Number(workspaceValues.radiusMeters),
      topic: String(workspaceValues.topic ?? "general"),
    },
    localPublicVisibility: { ...(localPublicVisibility ?? {}) },
    localPublicOpacity: { ...(localPublicOpacity ?? {}) },
    importedPublicLayers: importedPublicLayers.map((layer) => normalizeImportedPublicLayer(layer)),
    studentLayers: studentLayers.map((layer) => normalizeStudentLayer(layer)),
    reflectionNote: String(reflectionNote ?? ""),
    sgisControls: {
      metricId: String(sgisControls?.metricId ?? ""),
      year: Number(sgisControls?.year ?? 0),
      color: String(sgisControls?.color ?? "#1d9bf0"),
    },
    activeLayerId: activeLayerId ? String(activeLayerId) : null,
  };
}

export function normalizeWorkspaceProject(project, {
  normalizeWorkspaceValues,
  fallbackConfig,
  parseFiniteNumber,
  parsePositiveInteger,
  localPublicLayers,
}) {
  const normalizedWorkspaceValues = normalizeWorkspaceValues(project?.workspaceValues ?? {}, {
    fallbackConfig,
    parseFiniteNumber,
    parsePositiveInteger,
  });

  const normalizedStudentLayers = Array.isArray(project?.studentLayers)
    ? project.studentLayers.map((layer) => normalizeStudentLayer(layer))
    : [];
  const normalizedImportedPublicLayers = Array.isArray(project?.importedPublicLayers)
    ? project.importedPublicLayers.map((layer) => normalizeImportedPublicLayer(layer))
    : [];

  const selectedLayerExists = normalizedStudentLayers.some((layer) => layer.id === project?.activeLayerId);

  return {
    id: String(project?.id ?? ""),
    name: String(project?.name ?? "").trim() || "저장한 프로젝트",
    savedAt: project?.savedAt ?? new Date(0).toISOString(),
    viewMode: project?.viewMode === "korea" ? "korea" : "school",
    baseMapMode: String(project?.baseMapMode ?? "roadmap"),
    mapOverlayLayerIds: normalizeStringArray(project?.mapOverlayLayerIds),
    showSchoolReference: project?.showSchoolReference !== false,
    workspaceValues: normalizedWorkspaceValues,
    localPublicVisibility: normalizeLocalPublicVisibility(project?.localPublicVisibility, localPublicLayers),
    localPublicOpacity: normalizeLocalPublicOpacity(project?.localPublicOpacity, localPublicLayers),
    importedPublicLayers: normalizedImportedPublicLayers,
    studentLayers: normalizedStudentLayers,
    reflectionNote: String(project?.reflectionNote ?? ""),
    sgisControls: {
      metricId: String(project?.sgisControls?.metricId ?? ""),
      year: Number(project?.sgisControls?.year ?? 0),
      color: String(project?.sgisControls?.color ?? "#1d9bf0"),
    },
    activeLayerId: selectedLayerExists
      ? project.activeLayerId
      : normalizedStudentLayers[0]?.id ?? null,
  };
}

export function normalizeWorkspaceProjects(projects, normalizeProject) {
  return (Array.isArray(projects) ? projects : [])
    .map((project) => normalizeProject(project))
    .filter((project) => project.id);
}

export function upsertWorkspaceProject(projects, nextProject) {
  const remainingProjects = (Array.isArray(projects) ? projects : [])
    .filter((project) => project.id !== nextProject.id);
  return [nextProject, ...remainingProjects]
    .sort((left, right) => new Date(right.savedAt).getTime() - new Date(left.savedAt).getTime());
}

export function removeWorkspaceProject(projects, projectId) {
  return (Array.isArray(projects) ? projects : [])
    .filter((project) => project.id !== projectId);
}

export function buildWorkspaceProjectViewModel(projects, selectedProjectId) {
  const sortedProjects = [...(Array.isArray(projects) ? projects : [])]
    .sort((left, right) => new Date(right.savedAt).getTime() - new Date(left.savedAt).getTime());
  const selectedProject = sortedProjects.find((project) => project.id === selectedProjectId)
    ?? sortedProjects[0]
    ?? null;

  return {
    selectedProjectId: selectedProject?.id ?? "",
    selectedProjectHint: selectedProject
      ? `${selectedProject.name} · ${formatSavedAt(selectedProject.savedAt)} · 공공 ${selectedProject.importedPublicLayers.length} · 학생 ${selectedProject.studentLayers.length}`
      : "저장한 프로젝트가 없습니다.",
    projects: sortedProjects.map((project) => ({
      id: project.id,
      label: `${project.name} (${formatSavedAt(project.savedAt)})`,
      detail: `공공 ${project.importedPublicLayers.length} · 학생 ${project.studentLayers.length}`,
    })),
  };
}
