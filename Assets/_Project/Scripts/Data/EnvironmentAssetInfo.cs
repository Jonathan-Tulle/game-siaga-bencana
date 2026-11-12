using UnityEngine;

namespace SiagaBencana.EnvAssets
{
    public enum EnvironmentCategory
    {
        Building,
        Vegetation,
        Infrastructure,
        Props,
        Signage
    }

    /// <summary>
    /// Penanda kategori pada prefab environment.
    /// Dipakai programmer, misalnya untuk objek yang bergoyang saat gempa.
    /// </summary>
    [DisallowMultipleComponent]
    public class EnvironmentAssetInfo : MonoBehaviour
    {
        [SerializeField] private EnvironmentCategory category;
        [SerializeField] private bool shakesDuringEarthquake;

        public EnvironmentCategory Category => category;
        public bool ShakesDuringEarthquake => shakesDuringEarthquake;

        public void Setup(EnvironmentCategory cat, bool shakes)
        {
            category = cat;
            shakesDuringEarthquake = shakes;
        }
    }
}