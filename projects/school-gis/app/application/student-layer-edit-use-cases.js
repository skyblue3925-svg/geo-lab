import { normalizeStudentFeature, normalizeStudentLayer } from "../domain/student-layer.js";
import { buildFeatureMeasurementSummary } from "./measurement-use-cases.js";

function getSeverityLabel(value) {
  if (String(value) === "3") {
    return "높음";
  }
  if (String(value) === "1") {
    return "낮음";
  }
  return "보통";
}

function withFeatureMetrics(feature) {
  const measurementSummary = buildFeatureMeasurementSummary(feature);
  if (!measurementSummary) {
    return feature;
  }

  return {
    ...feature,
    properties: {
      ...feature.properties,
      ...measurementSummary,
    },
  };
}

export function appendFeatureToStudentLayers(studentLayers, layerId, feature) {
  return studentLayers.map((layer) =>
    layer.id === layerId
      ? normalizeStudentLayer({
          ...layer,
          features: [...layer.features, withFeatureMetrics(feature)],
        })
      : layer,
  );
}

export function updateStudentFeatureDetails(studentLayers, {
  layerId,
  featureId,
  title,
  note,
  severity,
  observedLabel,
  observedValue,
  observedUnit,
}) {
  return studentLayers.map((layer) => {
    if (layer.id !== layerId) {
      return layer;
    }

    return normalizeStudentLayer({
      ...layer,
      features: layer.features
        .map((feature) => {
          if (feature.id !== featureId) {
            return feature;
          }

          return withFeatureMetrics(
            normalizeStudentFeature({
              ...feature,
              title,
              note,
              properties: {
                ...feature.properties,
                severity: String(severity ?? feature.properties?.severity ?? "2"),
                severityLabel: getSeverityLabel(severity ?? feature.properties?.severity ?? "2"),
                observedLabel: String(observedLabel ?? feature.properties?.observedLabel ?? "").trim(),
                observedValue: String(observedValue ?? feature.properties?.observedValue ?? "").trim(),
                observedUnit: String(observedUnit ?? feature.properties?.observedUnit ?? "").trim(),
              },
            }, feature.geometryType),
          );
        })
        .filter(Boolean),
    });
  });
}

export function removeStudentFeature(studentLayers, layerId, featureId) {
  return studentLayers.map((layer) => {
    if (layer.id !== layerId) {
      return layer;
    }

    return normalizeStudentLayer({
      ...layer,
      features: layer.features.filter((feature) => feature.id !== featureId),
    });
  });
}
