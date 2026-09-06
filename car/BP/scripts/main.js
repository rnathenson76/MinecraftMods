// ============================================================
//  MONSTER TRUCK  —  nitro, horn and block-climbing
// ============================================================
//
// Driving (built-in): sit in it, then steer with the normal move joystick.
//
// This script adds the fun parts, all on the JUMP button:
//   - TAP jump (quick press)   -> HONK the horn
//   - HOLD jump                -> NITRO: a burst of speed + flames out the
//                                 exhaust stacks
//   - driving into a 1-block step -> the truck climbs it instead of stopping
//
// (Sneak can't be the horn: on Bedrock the sneak button is what gets you out
// of a vehicle, so tapping it would just make you hop out.)

import { world, system, InputButton, ButtonState } from "@minecraft/server";

const TRUCK = "vehicles:monster_truck";

// ---- Feel (tweak these!) ----
const TAP_TICKS = 5;       // press jump for fewer ticks than this = a honk
const NITRO_PUSH = 0.085;  // how hard nitro shoves the truck each tick
const NITRO_TOP_SPEED = 1.0;   // fastest nitro will push you (blocks/tick)
const CLIMB_PUSH = 0.52;   // how hard it hops up onto a block
const CLIMB_COOLDOWN = 6;  // ticks to wait between climbs
const HORN_SOUND = "note.didgeridoo";
const HORN_PITCH = 0.55;   // lower number = deeper horn
const HORN_COOLDOWN = 8;   // ticks, so holding the button can't machine-gun it

// remembers, per driver, how long jump has been held down
const drivers = new Map();

function flatForward(entity) {
  const v = entity.getViewDirection();
  const len = Math.hypot(v.x, v.z);
  if (len < 0.01) return { x: 0, z: 0 };
  return { x: v.x / len, z: v.z / len };
}

function honk(truck) {
  try {
    truck.dimension.playSound(HORN_SOUND, truck.location, {
      pitch: HORN_PITCH,
      volume: 1.4,
    });
  } catch (e) { /* sound not ready */ }
}

function nitro(truck) {
  const forward = flatForward(truck);
  const v = truck.getVelocity();

  if (Math.hypot(v.x, v.z) < NITRO_TOP_SPEED) {
    truck.applyImpulse({
      x: forward.x * NITRO_PUSH,
      y: 0,
      z: forward.z * NITRO_PUSH,
    });
  }

  // flames out of the two exhaust stacks behind the cab
  const loc = truck.location;
  for (const side of [-0.85, 0.85]) {
    try {
      truck.dimension.spawnParticle("minecraft:basic_flame_particle", {
        x: loc.x - forward.x * 0.5 + forward.z * side,
        y: loc.y + 4.7,
        z: loc.z - forward.z * 0.5 - forward.x * side,
      });
    } catch (e) { /* chunk not loaded */ }
  }
}

// climb a 1-block step instead of grinding to a halt against it
function climbStep(truck, state) {
  if (state.climbCooldown > 0) return;

  const v = truck.getVelocity();
  if (Math.hypot(v.x, v.z) < 0.05) return; // parked — nothing to climb

  const forward = flatForward(truck);
  const loc = truck.location;
  const x = Math.floor(loc.x + forward.x * 1.9);
  const z = Math.floor(loc.z + forward.z * 1.9);
  const y = Math.floor(loc.y);

  try {
    const inTheWay = truck.dimension.getBlock({ x, y, z });
    const oneUp = truck.dimension.getBlock({ x, y: y + 1, z });
    const twoUp = truck.dimension.getBlock({ x, y: y + 2, z });

    if (inTheWay?.isSolid && !oneUp?.isSolid && !twoUp?.isSolid) {
      truck.applyImpulse({ x: 0, y: CLIMB_PUSH, z: 0 });
      state.climbCooldown = CLIMB_COOLDOWN;
    }
  } catch (e) { /* block not loaded yet */ }
}

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const truck = player.getComponent("minecraft:riding")?.entityRidingOn;

    if (!truck || truck.typeId !== TRUCK) {
      drivers.delete(player.id);
      continue;
    }

    const state = drivers.get(player.id) ?? {
      held: 0,
      hornCooldown: 0,
      climbCooldown: 0,
    };
    if (state.hornCooldown > 0) state.hornCooldown--;
    if (state.climbCooldown > 0) state.climbCooldown--;

    try {
      const jumpDown =
        player.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed;

      if (jumpDown) {
        state.held++;
        if (state.held > TAP_TICKS) nitro(truck);
      } else {
        // just let go after a quick tap -> that's a honk
        if (state.held > 0 && state.held <= TAP_TICKS && state.hornCooldown === 0) {
          honk(truck);
          state.hornCooldown = HORN_COOLDOWN;
        }
        state.held = 0;
      }
    } catch (e) {
      // input hiccup — driving and climbing still work
    }

    climbStep(truck, state);
    drivers.set(player.id, state);
  }
}, 1);
