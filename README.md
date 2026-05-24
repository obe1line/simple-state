# CRTP State Machine for STM32F405 Bare-Metal Firmware

[![CI](https://github.com/obe1line/simple-state/actions/workflows/ci.yml/badge.svg)](https://github.com/obe1line/simple-state/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/obe1line/simple-state)](https://github.com/obe1line/simple-state/blob/main/LICENSE.html)
[![Latest Release](https://img.shields.io/github/v/release/obe1line/simple-state)](https://github.com/obe1line/simple-state/releases)

This repository contains a small C++20 state machine built with the curiously recurring template pattern (CRTP). The implementation is designed for bare-metal firmware on an STM32F405, but it also includes a host-side simulation and test target so the behavior can be verified on Linux.

## Why CRTP here?

The state machine avoids virtual dispatch and heap allocation:

- each state is a type
- state handlers are resolved at compile time
- the active state is represented by a small table of function pointers
- transitions are explicit and deterministic

That makes the pattern a good fit for microcontrollers where code size, predictability, and allocation-free behavior matter.

## Project layout

- `include/simple_state/crtp_state_machine.hpp`: reusable CRTP state machine core
- `include/simple_state/blinky_controller.hpp`: STM32-friendly example controller with `Boot`, `Idle`, `LedOn`, `LedOff`, and `Fault` states
- `include/simple_state/simulated_board.hpp`: host-side board shim used by the demo and tests
- `include/simple_state/stm32f405_hal_board.hpp`: concrete STM32F405 HAL adapter that satisfies the controller board interface
- `examples/stm32f405_hal_main.cpp`: firmware-style `main()` showing how to wire the controller into an STM32 startup flow
- `src/demo_main.cpp`: runnable simulation showing state transitions over time
- `tests/state_machine_test.cpp`: small assertion-based test harness
- `diagrams/blinky.mmd`: Mermaid source used to describe the blinky state graph
- `tools/mermaid_to_controller.py`: Mermaid-to-`hpp` controller generator
- `tools/compare_state_transitions.py`: parity checker for states/transitions between headers
- `CMakeLists.txt`: build configuration for demo and tests

## State flow

The example controller models a simple firmware LED task:

1. `Boot`
	- waits 100 ms for a self-test window
	- transitions to `Idle` on success
	- transitions to `Fault` on failure
2. `Idle`
	- keeps the LED off
	- waits for a button press or a 1 s timeout
3. `LedOn`
	- turns the LED on for 250 ms
4. `LedOff`
	- turns the LED off for 750 ms
5. `Fault`
	- blinks the LED every 100 ms

Any runtime fault detected after boot sends the machine into `Fault`.

## Build and run

Verified on Linux with `g++ 14` and CMake.

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
./build/stm32_state_demo
```

`ctest` also runs Mermaid parity checks that:
- generate `blinky_from_mermaid.hpp` from `diagrams/blinky.mmd`
- verify generated states/transitions match `include/simple_state/blinky_controller.hpp`

## Generate controller headers from Mermaid

The repository includes a small generator that converts Mermaid state transitions into a controller header scaffold compatible with `simple_state::Machine`.

Generate a controller header from a Mermaid diagram:

```bash
python3 tools/mermaid_to_controller.py \
	--input diagrams/blinky.mmd \
	--output generated/blinky_from_mermaid.hpp \
	--controller BlinkyController
```

Validate that the generated header contains the same states and transitions as the hand-written blinky controller:

```bash
python3 tools/compare_state_transitions.py \
	--expected include/simple_state/blinky_controller.hpp \
	--actual generated/blinky_from_mermaid.hpp
```

The comparison command reports `Comparison PASSED` when both state and transition sets are equal.

Expected demo output is similar to:

```text
t=0ms state=Boot led=0
t=100ms state=Idle led=0
t=300ms state=LedOn led=1
t=550ms state=LedOff led=0
t=1300ms state=LedOn led=1
t=1450ms state=Fault led=1
samples=11
```

## Using it on STM32F405

The controller is templated on a board type. This repository now includes a concrete adapter in `include/simple_state/stm32f405_hal_board.hpp`, and that adapter implements this board API:

```cpp
struct Stm32Board {
	 std::uint32_t millis() const;
	 void set_led(bool is_on);
	 bool led_is_on() const;
	 bool is_button_pressed() const;
	 bool has_fault() const;
	 bool self_test_ok() const;
};
```

For an STM32F405 project using HAL:

- `millis()` reads `HAL_GetTick()`
- `set_led()` writes the configured LED GPIO pin
- `is_button_pressed()` samples the configured button GPIO pin
- `has_fault()` and `self_test_ok()` read lightweight runtime flags you control from the rest of the firmware

The provided adapter is configured with a `Stm32f405HalBoardConfig`:

```cpp
simple_state::Stm32f405RuntimeFlags runtime_flags{};

const simple_state::Stm32f405HalBoardConfig board_config{
	.led_port = GPIOD,
	.led_pin = GPIO_PIN_12,
	.led_active_state = GPIO_PIN_SET,
	.button_port = GPIOA,
	.button_pin = GPIO_PIN_0,
	.button_pressed_state = GPIO_PIN_SET,
	.flags = &runtime_flags,
	.tick_reader = HAL_GetTick,
};
```

That mapping matches the common STM32F4 Discovery wiring of green LED on `PD12` and user button on `PA0`.

Example integration:

```cpp
#include "simple_state/blinky_controller.hpp"
#include "simple_state/stm32f405_hal_board.hpp"

simple_state::Stm32f405RuntimeFlags runtime_flags{};

const simple_state::Stm32f405HalBoardConfig board_config{
	.led_port = GPIOD,
	.led_pin = GPIO_PIN_12,
	.led_active_state = GPIO_PIN_SET,
	.button_port = GPIOA,
	.button_pin = GPIO_PIN_0,
	.button_pressed_state = GPIO_PIN_SET,
	.flags = &runtime_flags,
	.tick_reader = HAL_GetTick,
};

simple_state::Stm32f405HalBoard board{board_config};
simple_state::BlinkyController<simple_state::Stm32f405HalBoard> controller{board};

int main() {
	HAL_Init();
	SystemClock_Config();
	MX_GPIO_Init();

	runtime_flags.self_test_passed = run_power_on_self_test();
	 controller.start();

	 while (true) {
		controller.run_once();
	 }
}
```

See `examples/stm32f405_hal_main.cpp` for a complete firmware-oriented skeleton.

## STM32 integration notes

- `examples/stm32f405_hal_main.cpp` is intentionally not part of the Linux host build because it depends on STM32 HAL headers, startup files, and your cross-compilation toolchain.
- `SystemClock_Config()` and `MX_GPIO_Init()` are placeholders for your CubeMX- or hand-written board initialization.
- `Stm32f405RuntimeFlags` is deliberately simple so interrupt handlers or background checks can update fault status without coupling that logic to the controller.
- If you prefer the STM32 LL drivers instead of HAL, the same controller can be reused by swapping only the board adapter implementation.

## Notes for bare-metal use

- no dynamic allocation is used by the controller itself
- no RTTI or virtual functions are required
- `run_once()` is intended to be called from the main superloop
- transitions execute synchronously, which keeps behavior easy to reason about
- the host-side `SimulatedBoard` stores LED history in a `std::vector`, but that is only for testing and demo use

## Next extensions

If you want to push this further for production firmware, the next useful steps are:

- replace the simulated board with an STM32 HAL or LL adapter
- move fault causes into an enum for richer diagnostics
- add event queues or interrupt-fed flags if the system grows beyond polling
- add unit tests for button debounce and recovery behavior