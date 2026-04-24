export function getLeverGuideItems({ observedMode }) {
  return [
    {
      name: "월",
      effect: "두 모드 공통으로 현재 달을 바꿉니다.",
      detail: observedMode
        ? "기본 지도, 대기대순환, 선택 월 하이라이트와 관측 그래프를 같은 달 기준으로 읽게 합니다."
        : "지도, 대기대순환, 기온과 강수 맥락을 모두 같은 달 기준으로 다시 계산합니다.",
    },
    {
      name: "프리셋",
      effect: "수업용 대표 배치를 한 번에 바꾸는 묶음 설정입니다.",
      detail: observedMode
        ? "관측 모드에서는 잠겨 있으며 설명용 기본값만 참고합니다."
        : "대륙 배치, 기본 산맥, 해류, 대표 관찰 지점을 한 번에 바꿉니다.",
    },
    {
      name: "자전축 기울기",
      effect: "계절 대비와 ITCZ 이동 폭을 키우거나 줄입니다.",
      detail: observedMode
        ? "관측 지도와 실측 그래프는 유지되지만 대기대순환 설명은 그에 맞게 흔들립니다."
        : "여름·겨울의 온도차, 우기·건기 대비, 기압대 이동 폭이 함께 커집니다.",
    },
    {
      name: "대륙 크기",
      effect: "해양성인지 대륙성인지의 강도를 바꿉니다.",
      detail: observedMode
        ? "관측값 자체는 고정되고, 설명 패널에서 해양 영향·내륙 영향 해석만 달라집니다."
        : "대륙이 커질수록 연교차와 내륙 건조가 강해지고, 작아질수록 해양 완충이 커집니다.",
    },
    {
      name: "산맥 높이",
      effect: "고도 냉각, 바람받이 강수, 비그늘 효과를 조절합니다.",
      detail: observedMode
        ? "기본 지도에서는 산맥 점선을 숨기고, 실험 화면에서만 지형 효과를 설명합니다."
        : "높을수록 산맥 전면 강수와 후면 건조가 강해지고, 고산 냉각도 함께 커집니다.",
    },
    {
      name: "해류 효과",
      effect: "해안의 온도와 수분 공급을 따뜻한 쪽 또는 차가운 쪽으로 기웁니다.",
      detail: observedMode
        ? "관측값은 유지하지만 해안 설명과 대기·해양 해석에서 난류와 한류를 비교할 수 있습니다."
        : "난류는 온난·습윤 쪽으로, 한류는 냉량·건조 쪽으로 기후를 밀어줍니다.",
    },
  ];
}

export function getControlNote({
  observedMode,
  modeLabel,
  overlay,
  circulationStageLabel,
  circulationStageNote,
  activeClimateDataset,
}) {
  if (observedMode) {
    return overlay === "circulation"
      ? `현재는 ${modeLabel}입니다. 쾨펜 지도는 Beck et al. 2026 v2 1991-2020 공식 분류를 사용하고, 월별 차트는 ${activeClimateDataset.dataset} ${activeClimateDataset.period} ${activeClimateDataset.resolution} 자료를 따릅니다. 화면 조작은 그대로 두고, 대기순환은 ${circulationStageLabel} 단계로 학습합니다.`
      : `현재는 ${modeLabel}입니다. 공식 쾨펜 지도와 ${activeClimateDataset.dataset} ${activeClimateDataset.period} ${activeClimateDataset.resolution} 월별 자료를 그대로 읽습니다. 지도나 그래프 자체를 바꾸려면 실험실 화면으로 전환하세요.`;
  }

  return overlay === "circulation"
    ? `현재는 ${modeLabel}입니다. 프리셋, 자전축, 대륙 크기, 산맥, 해류 레버가 순환 셀과 기압대, 상층 제트, 지도 위 값을 다시 계산합니다. 지금 단계는 ${circulationStageLabel}입니다. ${circulationStageNote}`
    : `현재는 ${modeLabel}입니다. 프리셋, 자전축, 대륙 크기, 산맥, 해류 레버가 쾨펜 지도, 월별 기온·강수 그래프, 선택 지점 설명을 모두 다시 계산합니다.`;
}

export function buildControlPanelViewModel({
  state,
  screenMeta,
  mission,
  circulationStage,
  observedMode,
  modeMeta,
  monthLabels,
  presets,
  activeClimateDataset,
}) {
  return {
    screenModeId: screenMeta.id,
    screenModeNote: screenMeta.note,
    monthLabel: monthLabels[state.month - 1],
    tiltLabel: `${Number(state.tilt).toFixed(1)}°`,
    landScaleLabel: `${Math.round(state.landScale * 100)}%`,
    mountainHeightLabel: `${Math.round(state.mountainHeight).toLocaleString()} m`,
    currentBias: Number(state.currentBias),
    overlay: state.overlay,
    climateMode: state.climateMode,
    circulationStageId: circulationStage.id,
    circulationStageVisible: state.overlay === "circulation",
    observedMode,
    presetDescription: presets[state.presetId].description,
    guidedKnobs: new Set(mission.knobTargets),
    controlNote: getControlNote({
      observedMode,
      modeLabel: modeMeta.label,
      overlay: state.overlay,
      circulationStageLabel: circulationStage.label,
      circulationStageNote: circulationStage.note,
      activeClimateDataset,
    }),
  };
}
