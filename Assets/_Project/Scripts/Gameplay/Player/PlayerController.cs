using UnityEngine;
using UnityEngine.InputSystem;
using SiagaBencana.Core;

namespace SiagaBencana.Gameplay
{
    [RequireComponent(typeof(CharacterController))]
    public class PlayerController : MonoBehaviour
    {
        [SerializeField] private float _walkSpeed = 4.5f;
        [SerializeField] private float _sprintSpeed = 7.5f;
        [SerializeField] private float _coverSpeed = 2f;
        [SerializeField] private float _gravity = -20f;

        private CharacterController _controller;
        private Transform _visualTransform;

        private Vector2 _moveInput;
        private bool _sprintInput;
        private bool _isCovering;
        private float _verticalVelocity;

        public bool IsCovering => _isCovering;
        public bool IsInCoverZone { get; set; }
        public bool IsSafelyCovered => _isCovering && IsInCoverZone;
        public bool CanMove { get; set; } = true;

        private GameState _stateBeforePause;

        private void Awake()
        {
            _controller = GetComponent<CharacterController>();
            _visualTransform = transform.Find("Visual");
        }

        private void OnEnable()
        {
            GameEvents.OnGameStateChanged += HandleGameStateChanged;
        }

        private void OnDisable()
        {
            GameEvents.OnGameStateChanged -= HandleGameStateChanged;
        }

        private void Update()
        {
            if (!CanMove) return;

            ReadInput();
            HandleMovement();
        }

        private void ReadInput()
        {
            var kb = Keyboard.current;
            if (kb == null) return;

            _moveInput = Vector2.zero;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed)    _moveInput.y += 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed)  _moveInput.y -= 1f;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed)  _moveInput.x -= 1f;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) _moveInput.x += 1f;
            _moveInput = _moveInput.normalized;

            _sprintInput = kb.leftShiftKey.isPressed && !_isCovering;

            if (kb.cKey.wasPressedThisFrame)
            {
                ToggleCover();
            }

            if (kb.escapeKey.wasPressedThisFrame)
            {
                TogglePause();
            }
        }

        private void HandleMovement()
        {
            if (_controller.isGrounded && _verticalVelocity < 0f)
                _verticalVelocity = -1f;
            else
                _verticalVelocity += _gravity * Time.deltaTime;

            float speed = _isCovering ? _coverSpeed : (_sprintInput ? _sprintSpeed : _walkSpeed);
            Vector3 moveDirection = new Vector3(_moveInput.x, 0f, _moveInput.y);

            if (moveDirection.sqrMagnitude > 0.01f)
            {
                transform.rotation = Quaternion.LookRotation(moveDirection);
            }

            Vector3 velocity = moveDirection * speed;
            velocity.y = _verticalVelocity;
            _controller.Move(velocity * Time.deltaTime);
        }

        private void ToggleCover()
        {
            _isCovering = !_isCovering;

            if (_visualTransform != null)
            {
                if (_isCovering)
                {
                    _visualTransform.localScale = new Vector3(1f, 0.55f, 1f);
                    _visualTransform.localPosition = Vector3.zero;
                }
                else
                {
                    _visualTransform.localScale = Vector3.one;
                    _visualTransform.localPosition = Vector3.zero;
                }
            }

            GameEvents.RaisePlayerCoverChanged(_isCovering);
        }

        private void TogglePause()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;

            if (gm.CurrentState == GameState.Paused)
            {
                gm.ResumeGame(_stateBeforePause);
            }
            else
            {
                _stateBeforePause = gm.CurrentState;
                gm.PauseGame();
            }
        }

        private void HandleGameStateChanged(GameState newState)
        {
            CanMove = newState == GameState.Preparation ||
                      newState == GameState.Disaster ||
                      newState == GameState.PostDisaster;
        }
    }
}
