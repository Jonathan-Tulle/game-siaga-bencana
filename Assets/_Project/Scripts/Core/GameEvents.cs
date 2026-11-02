using System;

namespace SiagaBencana.Core
{
    public static class GameEvents
    {
        // Game State
        public static event Action<GameState> OnGameStateChanged;
        public static void RaiseGameStateChanged(GameState newState) =>
            OnGameStateChanged?.Invoke(newState);

        // Disaster
        public static event Action<DisasterType> OnDisasterStarted;
        public static void RaiseDisasterStarted(DisasterType type) =>
            OnDisasterStarted?.Invoke(type);

        public static event Action OnDisasterEnded;
        public static void RaiseDisasterEnded() =>
            OnDisasterEnded?.Invoke();

        public static event Action<EarthquakePhase> OnEarthquakePhaseChanged;
        public static void RaiseEarthquakePhaseChanged(EarthquakePhase phase) =>
            OnEarthquakePhaseChanged?.Invoke(phase);

        public static event Action<float> OnEarthquakeShakeIntensityChanged;
        public static void RaiseEarthquakeShakeIntensityChanged(float intensity) =>
            OnEarthquakeShakeIntensityChanged?.Invoke(intensity);

        // Player Cover
        public static event Action<bool> OnPlayerCoverChanged;
        public static void RaisePlayerCoverChanged(bool isCovering) =>
            OnPlayerCoverChanged?.Invoke(isCovering);

        // Decision
        public static event Action OnDecisionTriggered;
        public static void RaiseDecisionTriggered() =>
            OnDecisionTriggered?.Invoke();

        // Level Flow
        public static event Action OnPlayerReachedSafeZone;
        public static void RaisePlayerReachedSafeZone() =>
            OnPlayerReachedSafeZone?.Invoke();

        public static event Action<bool> OnLevelCompleted;
        public static void RaiseLevelCompleted(bool success) =>
            OnLevelCompleted?.Invoke(success);
    }
}
