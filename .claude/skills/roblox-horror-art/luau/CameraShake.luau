--!strict
-- CameraShake (ModuleScript, client): horror camera shake. Two sources add up:
--   * kick(amount): a burst that decays (a slam, a lunge hitting nearby, a scream);
--   * proximity: a rumble that rises as a tagged entity gets close (a rusher in
--     the corridor).
-- The shake is Perlin noise on "trauma" squared, so small amounts barely
-- register and large ones go violent quickly. It applies after Roblox's camera
-- scripts each frame, so it never accumulates.
--
-- Use, from a LocalScript:
--   local CameraShake = require(path.to.CameraShake)
--   CameraShake.start()
--   CameraShake.watch(entityModel, 60)   -- rumble within 60 studs
--   CameraShake.kick(0.6)

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local MAX_ANGLE = math.rad(4) -- degrees of roll/pitch/yaw at full trauma
local MAX_OFFSET = 0.35 -- studs of positional jitter at full trauma
local DECAY = 1.4 -- trauma lost per second
local FREQUENCY = 18 -- noise speed: higher reads as more erratic

local CameraShake = {}
local trauma = 0
local clock = 0
local watched: { [Model]: number } = {}

function CameraShake.kick(amount: number)
	trauma = math.min(1, trauma + amount)
end

-- Adds a rumble that grows from nothing at `radius` studs to full at contact.
function CameraShake.watch(entity: Model, radius: number)
	watched[entity] = radius
	entity.Destroying:Once(function()
		watched[entity] = nil
	end)
end

function CameraShake.unwatch(entity: Model)
	watched[entity] = nil
end

local function proximity(cameraPosition: Vector3): number
	local strongest = 0
	for entity, radius in watched do
		local distance = (entity:GetPivot().Position - cameraPosition).Magnitude
		strongest = math.max(strongest, 1 - math.clamp(distance / radius, 0, 1))
	end
	return strongest * 0.8 -- a rumble alone never reaches full violence
end

local function step(dt: number)
	local camera = workspace.CurrentCamera
	if not camera then
		return
	end
	clock += dt
	trauma = math.max(0, trauma - DECAY * dt)
	local amount = math.max(trauma, proximity(camera.CFrame.Position))
	local shake = amount * amount
	if shake <= 0 then
		return
	end
	local t = clock * FREQUENCY
	local n = function(seed: number): number
		return math.noise(t, seed) -- in roughly -1..1, smooth over time
	end
	camera.CFrame *= CFrame.new(n(1) * MAX_OFFSET * shake, n(2) * MAX_OFFSET * shake, 0)
		* CFrame.Angles(n(3) * MAX_ANGLE * shake, n(4) * MAX_ANGLE * shake, n(5) * MAX_ANGLE * shake)
end

function CameraShake.start()
	assert(RunService:IsClient(), "CameraShake runs on the client")
	RunService:BindToRenderStep("HorrorCameraShake", Enum.RenderPriority.Camera.Value + 1, step)
	Players.LocalPlayer.CharacterAdded:Connect(function()
		trauma = 0
	end)
end

function CameraShake.stop()
	RunService:UnbindFromRenderStep("HorrorCameraShake")
end

return CameraShake
