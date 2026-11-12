using UnityEngine;
using SiagaBencana.Core;

namespace SiagaBencana.Gameplay
{
    /// <summary>
    /// Mengontrol kamera isometrik/top-down: mengikuti pemain secara halus (smooth follow)
    /// dan menghasilkan efek getaran kamera gempa (camera shake) berbasis Perlin Noise organik
    /// sesuai spesifikasi GDD Bab 4.2 dan 4.8.
    /// </summary>
    public class CameraFollowController : MonoBehaviour
    {
        [Header("Target Follow")]
        [SerializeField] private Transform _target;
        [SerializeField] private Vector3 _offset = new Vector3(0f, 9f, -6f);
        [SerializeField] private float _smoothSpeed = 5f;

        [Header("Pengaturan Getaran Gempa (Camera Shake)")]
        [Tooltip("Frekuensi getaran per detik")]
        [SerializeField] private float _shakeFrequency = 22f;

        [Tooltip("Maksimum jarak pergeseran posisi kamera saat gempa dahsyat (meter)")]
        [SerializeField] private float _maxTranslationOffset = 0.45f;

        [Tooltip("Maksimum kemiringan rotasi roll kamera (derajat)")]
        [SerializeField] private float _maxRotationAngle = 1.25f;

        [Tooltip("Kecepatan transisi perubahan intensitas getaran")]
        [SerializeField] private float _intensityDamping = 6f;

        [Header("Aksesibilitas (GDD Bab 4.2 & 8.3)")]
        [Tooltip("Opsi aksesibilitas: getaran kamera dapat dinonaktifkan oleh pemain")]
        [SerializeField] private bool _enableShake = true;

        private Vector3 _currentVelocity;
        private Quaternion _baseRotation;
        private float _targetIntensity;
        private float _currentIntensity;
        private float _noiseSeedX;
        private float _noiseSeedY;
        private float _noiseSeedRot;

        public bool EnableShake
        {
            get => _enableShake;
            set => _enableShake = value;
        }

        public void SetTarget(Transform target) => _target = target;

        private void Awake()
        {
            // Seed acak agar getaran tidak monoton/repetitif
            _noiseSeedX = Random.Range(0f, 1000f);
            _noiseSeedY = Random.Range(1000f, 2000f);
            _noiseSeedRot = Random.Range(2000f, 3000f);
            _baseRotation = Quaternion.Euler(55f, 0f, 0f);
        }

        private void OnEnable()
        {
            GameEvents.OnEarthquakeShakeIntensityChanged += HandleShakeIntensityChanged;
            GameEvents.OnEarthquakePhaseChanged += HandleEarthquakePhaseChanged;
        }

        private void OnDisable()
        {
            GameEvents.OnEarthquakeShakeIntensityChanged -= HandleShakeIntensityChanged;
            GameEvents.OnEarthquakePhaseChanged -= HandleEarthquakePhaseChanged;
        }

        private void Start()
        {
            transform.rotation = _baseRotation;

            if (_target == null)
            {
                var player = FindAnyObjectByType<PlayerController>();
                if (player != null) _target = player.transform;
            }
        }

        private void LateUpdate()
        {
            if (_target == null) return;

            // 1. Perhitungan posisi dasar mengikuti pemain (Smooth Follow)
            Vector3 desiredPosition = _target.position + _offset;
            Vector3 basePosition = Vector3.SmoothDamp(
                transform.position, desiredPosition, ref _currentVelocity, 1f / _smoothSpeed);

            // 2. Interpolasi intensitas getaran secara halus
            _currentIntensity = Mathf.MoveTowards(
                _currentIntensity, _targetIntensity, _intensityDamping * Time.deltaTime);

            // 3. Hitung pergeseran posisi & rotasi jika guncangan aktif
            Vector3 shakeOffset = Vector3.zero;
            Quaternion shakeRotation = _baseRotation;

            if (_enableShake && _currentIntensity > 0.001f)
            {
                float time = Time.time * _shakeFrequency;

                // Perlin Noise kontinu untuk getaran translasi X dan Y yang natural
                float noiseX = (Mathf.PerlinNoise(_noiseSeedX + time, 0f) - 0.5f) * 2f;
                float noiseY = (Mathf.PerlinNoise(0f, _noiseSeedY + time) - 0.5f) * 2f;

                shakeOffset = new Vector3(
                    noiseX * _maxTranslationOffset * _currentIntensity,
                    noiseY * (_maxTranslationOffset * 0.6f) * _currentIntensity,
                    0f
                );

                // Sedikit guncangan rotasi (roll wobble) untuk memberikan sensasi tanah berguncang
                float noiseRot = (Mathf.PerlinNoise(_noiseSeedRot + time * 0.85f, 50f) - 0.5f) * 2f;
                float rotAngle = noiseRot * _maxRotationAngle * _currentIntensity;
                shakeRotation = _baseRotation * Quaternion.Euler(0f, 0f, rotAngle);
            }

            // 4. Terapkan hasil posisi dan orientasi kamera
            transform.position = basePosition + shakeOffset;
            transform.rotation = shakeRotation;
        }

        /// <summary>
        /// Menerima perubahan intensitas guncangan gempa dari EarthquakeController
        /// </summary>
        private void HandleShakeIntensityChanged(float intensity)
        {
            _targetIntensity = Mathf.Clamp01(intensity);
        }

        private void HandleEarthquakePhaseChanged(EarthquakePhase phase)
        {
            if (phase == EarthquakePhase.Ended)
            {
                _targetIntensity = 0f;
            }
        }

        /// <summary>
        /// Memicu guncangan sesaat (misalnya untuk aftershock atau puing jatuh)
        /// </summary>
        public void TriggerImpulseShake(float intensity, float duration = 0.5f)
        {
            _targetIntensity = Mathf.Clamp01(intensity);
            CancelInvoke(nameof(ResetShake));
            Invoke(nameof(ResetShake), duration);
        }

        private void ResetShake()
        {
            _targetIntensity = 0f;
        }
    }
}
