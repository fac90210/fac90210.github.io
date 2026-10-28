--!nonstrict
-- HeadTracking (ModuleScript): turns an entity's Neck and Head bones toward a
-- target on top of whatever animation is playing. It offsets each Bone's
-- CFrame (its rest offset), which the Animator never writes; the Animator
-- writes Bone.Transform, so the clip and the look-at stack without fighting.
--
-- Use (client-side for smoothness; bone offsets made on a client are visual only):
--   local HeadTracking = require(path.to.HeadTracking)
--   local look = HeadTracking.new(entityModel, neckBone, headBone, { snap = true })
--   look:setTarget(player.Character.Head)
--   ...
--   look:destroy()
--
-- Bone axes after FBX import can differ from Blender's. Check once in Studio
-- (see reference/rigging.md) and set yawAxis / pitchAxis, flipping the sign
-- of an axis if the head turns away from the target.

local RunService = game:GetService("RunService")

export type Config = {
	yawAxis: Vector3?, -- bone-local axis that turns the head left/right
	pitchAxis: Vector3?, -- bone-local axis that nods it up/down
	maxYaw: number?, -- degrees either side of the model's facing
	maxPitch: number?, -- degrees up or down
	speed: number?, -- follow rate; higher is quicker
	neckShare: number?, -- part of the turn the neck takes (the head takes the rest)
	snap: boolean?, -- uncanny mode: hold still, then jerk to the target
	snapAngle: number?, -- degrees of error that set off a snap
}

type Joint = { bone: Bone, rest: CFrame, share: number }

local HeadTracking = {}
HeadTracking.__index = HeadTracking

function HeadTracking.new(model: Model, neck: Bone, head: Bone, config: Config?)
	local c: Config = config or {}
	local neckShare = c.neckShare or 0.4
	local self = setmetatable({
		model = model,
		head = head,
		joints = {
			{ bone = neck, rest = neck.CFrame, share = neckShare },
			{ bone = head, rest = head.CFrame, share = 1 - neckShare },
		} :: { Joint },
		yawAxis = c.yawAxis or Vector3.yAxis,
		pitchAxis = c.pitchAxis or Vector3.xAxis,
		maxYaw = math.rad(c.maxYaw or 80),
		maxPitch = math.rad(c.maxPitch or 35),
		speed = c.speed or 6,
		snap = c.snap or false,
		snapAngle = math.rad(c.snapAngle or 25),
		snapping = false,
		yaw = 0,
		pitch = 0,
		target = nil :: BasePart?,
		connection = nil :: RBXScriptConnection?,
	}, HeadTracking)

	-- PreRender exists on clients only; a server script steps on Heartbeat.
	local signal = if RunService:IsClient() then RunService.PreRender else RunService.Heartbeat
	self.connection = signal:Connect(function(dt: number)
		self:_step(dt)
	end)
	return self
end

function HeadTracking:setTarget(target: BasePart?)
	self.target = target
end

-- The yaw and pitch, in the model's own frame, that would face the target;
-- zero when there's no target or it is behind the entity's reach.
function HeadTracking:_desired(): (number, number)
	local target = self.target
	if not target or not target.Parent then
		return 0, 0
	end
	local rel = self.model:GetPivot():VectorToObjectSpace(target.Position - self.head.WorldPosition)
	local yaw = math.atan2(-rel.X, -rel.Z) -- a model faces -Z (its LookVector)
	local pitch = math.atan2(rel.Y, Vector2.new(rel.X, rel.Z).Magnitude)
	if math.abs(yaw) > self.maxYaw * 1.4 then
		return 0, 0 -- too far behind: lose interest and face forward
	end
	return math.clamp(yaw, -self.maxYaw, self.maxYaw), math.clamp(pitch, -self.maxPitch, self.maxPitch)
end

function HeadTracking:_step(dt: number)
	local yaw, pitch = self:_desired()
	local err = math.max(math.abs(yaw - self.yaw), math.abs(pitch - self.pitch))
	local speed = self.speed
	if self.snap then
		-- Hold until the target has moved well away, then close the gap at once.
		if err > self.snapAngle then
			self.snapping = true
		elseif err < math.rad(1.5) then
			self.snapping = false
		end
		speed = if self.snapping then 40 else 0
	end
	local alpha = 1 - math.exp(-speed * dt) -- the same feel at any frame rate
	self.yaw += (yaw - self.yaw) * alpha
	self.pitch += (pitch - self.pitch) * alpha
	for _, joint in self.joints do
		joint.bone.CFrame = joint.rest
			* CFrame.fromAxisAngle(self.yawAxis, self.yaw * joint.share)
			* CFrame.fromAxisAngle(self.pitchAxis, self.pitch * joint.share)
	end
end

function HeadTracking:destroy()
	if self.connection then
		self.connection:Disconnect()
		self.connection = nil
	end
	for _, joint in self.joints do
		joint.bone.CFrame = joint.rest
	end
end

return HeadTracking
