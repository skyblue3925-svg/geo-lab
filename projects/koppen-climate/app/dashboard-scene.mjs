export function buildDashboardScene({
  state,
  buildScenarioFromState,
  buildWorld,
  analyzeLocation,
  finalizeAnalysisForMode,
}) {
  const scenario = buildScenarioFromState();
  const world = buildWorld(scenario);
  const analysis = finalizeAnalysisForMode(
    analyzeLocation(state.selectedLatitude, state.selectedLongitude, scenario),
  );
  return { scenario, world, analysis };
}
