using UnityEngine;
using SiagaBencana.Core;

namespace SiagaBencana.Gameplay
{
    /// <summary>
    /// Area perlindungan kokoh (seperti di bawah meja kokoh pada GDD Bab 4.8).
    /// Mendeteksi keberadaan pemain dan memvalidasi apakah pemain sedang menerapkan
    /// prosedur Drop, Cover, Hold On secara benar.
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class CoverZone : MonoBehaviour
    {
        private void OnTriggerEnter(Collider other)
        {
            var player = other.GetComponent<PlayerController>();
            if (player != null)
            {
                player.IsInCoverZone = true;
                Debug.Log("[CoverZone] Masuk ke bawah meja kokoh! Tekan C untuk berlindung (Drop, Cover, Hold On).");
            }
        }

        private void OnTriggerExit(Collider other)
        {
            var player = other.GetComponent<PlayerController>();
            if (player != null)
            {
                player.IsInCoverZone = false;
                Debug.Log("[CoverZone] Keluar dari bawah meja kokoh.");
            }
        }
    }
}
