export function createSelectedFeatureRef(layerId, featureId) {
  if (!layerId || !featureId) {
    return null;
  }

  return { layerId, featureId };
}

export function isSameSelectedFeatureRef(left, right) {
  return Boolean(
    left
    && right
    && left.layerId === right.layerId
    && left.featureId === right.featureId,
  );
}

export function findSelectedStudentFeature(studentLayers, selectedFeatureRef) {
  if (!selectedFeatureRef) {
    return null;
  }

  const layer = studentLayers.find((candidate) => candidate.id === selectedFeatureRef.layerId);
  if (!layer) {
    return null;
  }

  const feature = layer.features.find((candidate) => candidate.id === selectedFeatureRef.featureId);
  if (!feature) {
    return null;
  }

  return { layer, feature };
}
