using UnityEngine;
using SiagaBencana.Core;

namespace SiagaBencana.Gameplay
{
    /// <summary>
    /// Mengontrol siklus gempa bumi, intensitas guncangan bertahap (3 tingkat intensitas sesuai GDD 4.8),
    /// serta memicu dilema mitigasi Drop, Cover, Hold On.
    /// </summary>
    public class EarthquakeController : MonoBehaviour
    {
        [Header("Durasi & Parameter Gempa")]
        [Tooltip("Total durasi guncangan gempa bumi dalam detik")]
        [SerializeField] private float _earthquakeDuration = 12f;

        [Header("3 Tingkat Intensitas Guncangan (GDD Bab 4.8)")]
        [Range(0.1f, 0.4f)]
        [SerializeField] private float _initialIntensity = 0.25f;   // Fase 1: Guncangan awal
        [Range(0.4f, 1.0f)]
        [SerializeField] private float _peakIntensity = 0.65f;      // Fase 2: Guncangan puncak
        [Range(0.1f, 0.4f)]
        [SerializeField] private float _fadeIntensity = 0.20f;      // Fase 3: Guncangan mereda

        private EarthquakePhase _currentPhase = EarthquakePhase.Idle;
        private float _timer;
        private bool _isActive;
        private bool _decisionTriggered;
        private float _currentIntensity;

        public EarthquakePhase CurrentPhase => _currentPhase;
        public float CurrentIntensity => _currentIntensity;

        private void OnEnable()
        {
            GameEvents.OnDisasterStarted += HandleDisasterStarted;
        }

        private void OnDisable()
        {
            GameEvents.OnDisasterStarted -= HandleDisasterStarted;
        }

        private void Update()
        {
            if (!_isActive) return;

            _timer -= Time.deltaTime;
            float elapsed = _earthquakeDuration - _timer;

            // Hitung 3 tingkat intensitas secara dinamis (GDD 4.8)
            UpdateShakeIntensity(elapsed);

            // Memicu dilema keputusan mitigasi pada detik ke-1 guncangan
            if (!_decisionTriggered && elapsed >= 1f)
            {
                _decisionTriggered = true;
                GameEvents.RaiseDecisionTriggered();
            }

            // Guncangan gempa berakhir
            if (_timer <= 0f)
            {
                EndEarthquake();
            }
        }

        /// <summary>
        /// Menghitung kurva intensitas gempa bumi:
        /// 1. Awal (0 - 2.5s): Guncangan awal terasa (Low)
        /// 2. Puncak (2.5 - 8.5s): Guncangan keras / bahaya benda jatuh (Peak)
        /// 3. Akhir (8.5 - 12s): Guncangan mereda perlahan sebelum berhenti (Fade)
        /// </summary>
        private void UpdateShakeIntensity(float elapsed)
        {
            if (elapsed < 2.5f)
            {
                float t = elapsed / 2.5f;
                _currentIntensity = Mathf.Lerp(0.1f, _initialIntensity, t);
            }
            else if (elapsed < 8.5f)
            {
                _currentIntensity = _peakIntensity;
            }
            else
            {
                float t = (elapsed - 8.5f) / Mathf.Max(0.1f, _earthquakeDuration - 8.5f);
                _currentIntensity = Mathf.Lerp(_peakIntensity, _fadeIntensity, t);
            }

            GameEvents.RaiseEarthquakeShakeIntensityChanged(_currentIntensity);
        }

        private void HandleDisasterStarted(DisasterType type)
        {
            if (type != DisasterType.Earthquake) return;

            _isActive = true;
            _decisionTriggered = false;
            _currentPhase = EarthquakePhase.Shaking;
            _timer = _earthquakeDuration;
            _currentIntensity = _initialIntensity;

            GameEvents.RaiseEarthquakePhaseChanged(EarthquakePhase.Shaking);
            GameEvents.RaiseEarthquakeShakeIntensityChanged(_currentIntensity);
        }

        private void EndEarthquake()
        {
            _isActive = false;
            _currentIntensity = 0f;
            _currentPhase = EarthquakePhase.Ended;

            GameEvents.RaiseEarthquakeShakeIntensityChanged(0f);
            GameEvents.RaiseEarthquakePhaseChanged(EarthquakePhase.Ended);
            GameManager.Instance.StartPostDisasterPhase();
        }
    }
}
