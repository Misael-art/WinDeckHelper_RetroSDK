<?xml version="1.0"?>
<instrumentationManifest xsi:schemaLocation="http://schemas.microsoft.com/win/2004/08/events eventman.xsd" xmlns="http://schemas.microsoft.com/win/2004/08/events" xmlns:win="http://manifests.microsoft.com/win/2004/08/windows/events" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:trace="http://schemas.microsoft.com/win/2004/08/events/trace">
	<instrumentation>
		<events>
			<provider name="AMD-Kernel" guid="{33AEC352-AA8D-4905-B5AE-DBFF3B5F369D}" symbol="AMD_KERNEL_GUID" resourceFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" messageFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" parameterFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys ">
				<events>
					<event symbol="FlipPrimary" value="0" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="FlipPrimary" opcode="FlipPrimary" template="FlipPrimary" message="$(string.AMD-Kernel.event.0.message)">
					</event>
					<event symbol="VSync" value="1" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="VSync" opcode="VSync" template="VSync" message="$(string.AMD-Kernel.event.1.message)">
					</event>
					<event symbol="GfxQueueScheduler" value="2" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="GfxQueueScheduler" opcode="GfxQueueScheduler" template="GfxQueueScheduler" message="$(string.AMD-Kernel.event.2.message)">
					</event>
					<event symbol="TurboSyncCopyStart" value="3" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncCopyStart" opcode="TurboSync" template="TurboSyncCopyStart" message="$(string.AMD-Kernel.event.TurboSyncEventMap.CopyStart.message)">
					</event>
					<event symbol="TurboSyncCopyEnd" value="4" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncCopyEnd" opcode="TurboSync" template="TurboSyncCopyEnd" message="$(string.AMD-Kernel.event.TurboSyncEventMap.CopyEnd.message)">
					</event>
					<event symbol="TurboSyncVsync" value="5" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncVsync" opcode="TurboSync" template="TurboSync" message="$(string.AMD-Kernel.event.TurboSyncEventMap.Vsync.message)">
					</event>
					<event symbol="TurboSyncTimerHeld" value="6" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncTimerHeld" opcode="TurboSync" template="TurboSync" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeHeld.message)">
					</event>
					<event symbol="TurboSyncTimerSkip" value="7" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncTimerSkip" opcode="TurboSync" template="TurboSync" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeSkip.message)">
					</event>
					<event symbol="TurboSyncTimerRelease" value="8" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncTimerRelease" opcode="TurboSync" template="TurboSync" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeRelease.message)">
					</event>
					<event symbol="TurboSyncTimerTimeout" value="9" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncTimerTimeout" opcode="TurboSync" template="TurboSync" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeTimeout.message)">
					</event>
					<event symbol="TurboSyncFlipVsync" value="10" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncFlipVsync" opcode="TurboSync" template="TurboSyncFlip" message="$(string.AMD-Kernel.event.TurboSyncEventMap.FlipVsync.message)">
					</event>
					<event symbol="TurboSyncFlipImmediate" value="11" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncFlipImmediate" opcode="TurboSync" template="TurboSyncFlip" message="$(string.AMD-Kernel.event.TurboSyncEventMap.FlipImmediate.message)">
					</event>
					<event symbol="TurboSyncAverageFrameTime" value="12" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncAverageFrameTime" opcode="TurboSync" template="TurboSyncAverageFrameTime" message="$(string.AMD-Kernel.event.TurboSyncEventMap.AverageFrameTime.message)">
					</event>
					<event symbol="TurboSyncCheckFreeSyncActive" value="13" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncCheckFreeSyncActive" opcode="TurboSync" template="TurboSyncCheckFreeSyncActive" message="$(string.AMD-Kernel.event.TurboSyncEventMap.CheckFreeSyncActive.message)">
					</event>
					<event symbol="TurboSyncFlipQueueWorkItemToRetry" value="14" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncFlipQueueWorkItemToRetry" opcode="TurboSync" template="TurboSync" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TurboSyncFlipQueueWorkItemToRetry.message)">
					</event>
					<event symbol="TurboSyncFlipRetryAtPassive" value="15" version="0" channel="AMD-Kernel-Provider/Analytic" level="win:Informational" task="TurboSyncFlipRetryAtPassive" opcode="TurboSync" template="TurboSync" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TurboSyncFlipRetryAtPassive.message)">
					</event>
				</events>
				<levels>
				</levels>
				<tasks>
					<task name="FlipPrimary" symbol="TASK_FLIPPRIMARY" value="1" eventGUID="{62EEB1AE-AA7C-427D-AA47-D218A1385F2E}">
					</task>
					<task name="VSync" symbol="TASK_VSYNC" value="2" eventGUID="{855FF603-4C4D-4864-BA85-ED8066288B28}">
					</task>
					<task name="GfxQueueScheduler" symbol="TASK_GFXQUEUESCHEDULER" value="3" eventGUID="{67092F47-684C-4171-880C-1AD31165546E}">
					</task>
					<task name="TurboSyncCopyStart" symbol="TASK_TURBOSYNC_COPYSTART" value="4" eventGUID="{2D4B4B1B-24F1-4B91-AB5C-F69303FAF34E}">
					</task>
					<task name="TurboSyncCopyEnd" symbol="TASK_TURBOSYNC_COPYEND" value="5" eventGUID="{A15CC7A6-9BA7-4A41-A0F8-7CEC3358B554}">
					</task>
					<task name="TurboSyncVsync" symbol="TASK_TURBOSYNC_VSYNC" value="6" eventGUID="{11FF9F37-0A45-4E30-A636-04E6672121DB}">
					</task>
					<task name="TurboSyncTimerHeld" symbol="TASK_TURBOSYNC_TIMER_HELD" value="7" eventGUID="{7D184A3A-6C97-4E56-8805-A01E5C4ED90B}">
					</task>
					<task name="TurboSyncTimerSkip" symbol="TASK_TURBOSYNC_TIMER_SKIP" value="8" eventGUID="{68C43509-DBFD-4B75-A9C9-1FAEE61E7AA8}">
					</task>
					<task name="TurboSyncTimerRelease" symbol="TASK_TURBOSYNC_TIMER_RELEASE" value="9" eventGUID="{51405213-E6BB-4157-8391-A8F2AE3614D4}">
					</task>
					<task name="TurboSyncTimerTimeout" symbol="TASK_TURBOSYNC_TIMER_TIMEOUT" value="10" eventGUID="{E88A940B-DC2F-4362-A41F-D70D930AAC5B}">
					</task>
					<task name="TurboSyncFlipVsync" symbol="TASK_TURBOSYNC_FLIP_VSYNC" value="11" eventGUID="{C705C0AB-7080-4E8B-B0B1-8FAED847F9F2}">
					</task>
					<task name="TurboSyncFlipImmediate" symbol="TASK_TURBOSYNC_FLIP_IMMEDIATE" value="12" eventGUID="{94F4FC1B-769A-47E9-97D9-F46636CA53F3}">
					</task>
					<task name="TurboSyncAverageFrameTime" symbol="TASK_TURBOSYNC_AVERAGE_FRAME_TIME" value="13" eventGUID="{1CDB9F49-B113-4F51-A477-A126E7FA0F91}">
					</task>
					<task name="TurboSyncCheckFreeSyncActive" symbol="TASK_TURBOSYNC_CHECK_FREESYNC_ACTIVE" value="14" eventGUID="{BB39B7EC-3AAA-43A0-9CE1-7C2116758A99}">
					</task>
					<task name="TurboSyncFlipQueueWorkItemToRetry" symbol="TASK_TURBOSYNC_FLIP_QUEUE_WORKITEM_TO_RETRY" value="15" eventGUID="{2487C125-087B-4D13-A21B-CDD4571C63FF}">
					</task>
					<task name="TurboSyncFlipRetryAtPassive" symbol="TASK_TURBOSYNC_FLIP_RETRY_AT_PASSIVE" value="16" eventGUID="{19523338-9ACD-42AD-9AD7-37E2092194EC}">
					</task>
				</tasks>
				<opcodes>
					<opcode name="FlipPrimary" symbol="OPCODE_FLIP_PRIMARY" value="10">
					</opcode>
					<opcode name="VSync" symbol="OPCODE_VSYNC" value="11">
					</opcode>
					<opcode name="GfxQueueScheduler" symbol="OPCODE_GFXQUEUESCHEDULER" value="12">
					</opcode>
					<opcode name="TurboSync" symbol="OPCODE_TURBOSYNC" value="13">
					</opcode>
				</opcodes>
				<channels>
					<channel name="AMD-Kernel-Provider/Analytic" chid="AMD-Kernel-Provider/Analytic" symbol="CHANNEL_ANALYTIC" type="Analytic" enabled="false" message="$(string.AMD-Kernel.channel.CHANNEL_ANALYTIC.message)">
					</channel>
				</channels>
				<maps>
					<valueMap name="GfxQueueSchedulerMap">
						<map value="1" message="$(string.AMD-Kernel.event.GfxQueueScheduler.OsPreemption.message)">
						</map>
						<map value="2" message="$(string.AMD-Kernel.event.GfxQueueScheduler.QueueWorkItem.message)">
						</map>
						<map value="3" message="$(string.AMD-Kernel.event.GfxQueueScheduler.WorkItemCbEnter.message)">
						</map>
						<map value="4" message="$(string.AMD-Kernel.event.GfxQueueScheduler.WorkItemCbExit.message)">
						</map>
						<map value="5" message="$(string.AMD-Kernel.event.GfxQueueScheduler.ToHigh.message)">
						</map>
						<map value="6" message="$(string.AMD-Kernel.event.GfxQueueScheduler.ToLow.message)">
						</map>
					</valueMap>
					<valueMap name="TurboSyncEventMap">
						<map value="1" message="$(string.AMD-Kernel.event.TurboSyncEventMap.CopyStart.message)">
						</map>
						<map value="2" message="$(string.AMD-Kernel.event.TurboSyncEventMap.CopyEnd.message)">
						</map>
						<map value="3" message="$(string.AMD-Kernel.event.TurboSyncEventMap.Vsync.message)">
						</map>
						<map value="4" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeHeld.message)">
						</map>
						<map value="5" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeSkip.message)">
						</map>
						<map value="6" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeRelease.message)">
						</map>
						<map value="7" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TimerNodeTimeout.message)">
						</map>
						<map value="8" message="$(string.AMD-Kernel.event.TurboSyncEventMap.FlipVsync.message)">
						</map>
						<map value="9" message="$(string.AMD-Kernel.event.TurboSyncEventMap.FlipImmediate.message)">
						</map>
						<map value="10" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TurboSyncFlipQueueWorkItemToRetry.message)">
						</map>
						<map value="11" message="$(string.AMD-Kernel.event.TurboSyncEventMap.TurboSyncFlipRetryAtPassive.message)">
						</map>
					</valueMap>
				</maps>
				<templates>
					<template tid="FlipPrimary">
						<data name="VidPnTargetId" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="hAllocation" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="PrimaryAddress" inType="win:UInt64" outType="xs:unsignedLong">
						</data>
					</template>
					<template tid="VSync">
						<data name="Type" inType="win:Int32" outType="xs:int">
						</data>
						<data name="VidPnTargetId" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="GfxQueueScheduler">
						<data name="Type" inType="win:UInt32" map="GfxQueueSchedulerMap">
						</data>
					</template>
					<template tid="TurboSync">
						<data name="Type" inType="win:UInt32" map="TurboSyncEventMap">
						</data>
					</template>
					<template tid="TurboSyncCopyStart">
						<data name="SrcAddr" inType="win:UInt64" outType="win:HexInt64">
						</data>
						<data name="DestAddr" inType="win:UInt64" outType="win:HexInt64">
						</data>
						<data name="Fence" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="TurboSyncCopyEnd">
						<data name="FenceReturned" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="TurboSyncFlip">
						<data name="PrimaryAddr" inType="win:UInt64" outType="win:HexInt64">
						</data>
						<data name="hAllocation" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="PrimaryAddrOriginal" inType="win:UInt64" outType="win:HexInt64">
						</data>
						<data name="hAllocationOriginal" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="CallerId" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Blank Start" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="Blank End" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="Current VLine" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="TurboSyncAverageFrameTime">
						<data name="RawFrameTime" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="FilteredFrameTime" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="TurboSyncCheckFreeSyncActive">
						<data name="RawFlipInterval" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="FilteredFlipInterval" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="FreeSyncActivated" inType="win:Boolean" outType="xs:boolean">
						</data>
					</template>
				</templates>
			</provider>

                 <!--  ***************************** PPLib Events *************************** -->   
			<provider name="AMD-Kernel-PPLib" guid="{33AC52D0-EFF0-492E-8450-1025590F0C4B}" symbol="AMD_KERNEL_PPLib_GUID" resourceFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" messageFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" parameterFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys ">
				<events>
					<event symbol="General" value="0" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="General" template="PPLog">
					</event>
					<event symbol="ClockGating" value="2" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="ClockGating" template="PPLog">
					</event>
					<event symbol="PowerGating" value="3" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="PowerGating" template="PPLog">
					</event>
					<event symbol="DPM" value="4" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="DPM" template="PPLog">
					</event>
					<event symbol="IPS" value="5" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="IPS" template="PPLog">
					</event>
					<event symbol="ThermalControl" value="6" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="ThermalControl" template="PPLog">
					</event>
					<event symbol="OverDrive" value="7" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="OverDrive" template="PPLog">
					</event>
					<event symbol="SCLKLimitation" value="8" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="SCLKLimitation" template="PPLog">
					</event>
					<event symbol="FFC" value="9" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="FFC" template="PPLog">
					</event>
					<event symbol="FPS" value="10" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="FPS" template="PPLog">
					</event>
					<event symbol="AutomaticDCTransition" value="11" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="AutomaticDCTransition" template="PPLog">
					</event>
					<event symbol="ContextBasedPowerManagement" value="12" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="ContextBasedPowerManagement" template="PPLog">
					</event>
					<event symbol="SMCOperation" value="13" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="SMCOperation" template="PPLog">
					</event>
					<event symbol="PPStateOperation" value="14" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="PPStateOperation" template="PPLog">
					</event>
					<event symbol="CWDDEPM" value="15" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="CWDDEPM" template="PPLog">
					</event>
					<event symbol="IRI" value="16" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="IRI" template="PPLog">
					</event>
					<event symbol="InterruptRoutine" value="17" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="InterruptRoutine" template="PPLog">
					</event>
					<event symbol="EventChainAndTask" value="18" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="EventChainAndTask" template="PPLog">
					</event>
					<event symbol="SMCTable" value="19" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="SMCTable" template="PPLog">
					</event>
					<event symbol="RegRead" value="20" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="RegRead" template="PPLog">
					</event>
					<event symbol="RegWrite" value="21" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="RegWrite" template="PPLog">
					</event>
					<event symbol="Lock" value="22" version="0" channel="AMD-Kernel-PPLib-Provider/Analytic" level="win:Informational" task="PPLog" opcode="Lock" template="PPLog">
					</event>
					<event symbol="EventDumpCwddepm" value="23" version="0" level="win:Informational" opcode="EventDumpCwddepm" template="EventDumpCwddepm">
					</event>
					<event symbol="EventDumpPPIri" value="24" version="0" level="win:Informational" opcode="EventDumpIri" template="EventDumpPPIri">
					</event>
					<event symbol="EventDumpInputPayload" value="25" version="0" level="win:Informational" opcode="EventDumpPayloadInput" template="EventDumpPayloadInput">
					</event>
				</events>
				<levels>
				</levels>
				<tasks>
					<task name="PPLog" symbol="TASK_PPLog" value="1" eventGUID="{B885942E-B4D7-4D42-9E52-D754108BF756}">
					</task>
				</tasks>
				<opcodes>
					<opcode name="General" symbol="OPCODE_General" value="10">
					</opcode>
					<opcode name="ClockGating" symbol="OPCODE_ClockGating" value="12">
					</opcode>
					<opcode name="PowerGating" symbol="OPCODE_PowerGating" value="13">
					</opcode>
					<opcode name="DPM" symbol="OPCODE_DPM" value="14">
					</opcode>
					<opcode name="IPS" symbol="OPCODE_IPS" value="15">
					</opcode>
					<opcode name="ThermalControl" symbol="OPCODE_ThermalControl" value="16">
					</opcode>
					<opcode name="OverDrive" symbol="OPCODE_OverDrive" value="17">
					</opcode>
					<opcode name="SCLKLimitation" symbol="OPCODE_SCLKLimitation" value="18">
					</opcode>
					<opcode name="FFC" symbol="OPCODE_FFC" value="19">
					</opcode>
					<opcode name="FPS" symbol="OPCODE_FPS" value="20">
					</opcode>
					<opcode name="AutomaticDCTransition" symbol="OPCODE_AutomaticDCTransition" value="21">
					</opcode>
					<opcode name="ContextBasedPowerManagement" symbol="OPCODE_ContextBasedPowerManagement" value="22">
					</opcode>
					<opcode name="SMCOperation" symbol="OPCODE_SMCOperation" value="23">
					</opcode>
					<opcode name="PPStateOperation" symbol="OPCODE_PPStateOperation" value="24">
					</opcode>
					<opcode name="CWDDEPM" symbol="OPCODE_CWDDEPM" value="25">
					</opcode>
					<opcode name="IRI" symbol="OPCODE_IRI" value="26">
					</opcode>
					<opcode name="InterruptRoutine" symbol="OPCODE_InterruptRoutine" value="27">
					</opcode>
					<opcode name="EventChainAndTask" symbol="OPCODE_EventChainAndTask" value="28">
					</opcode>
					<opcode name="SMCTable" symbol="OPCODE_SMCTable" value="29">
					</opcode>
					<opcode name="RegRead" symbol="OPCODE_RegRead" value="30">
					</opcode>
					<opcode name="RegWrite" symbol="OPCODE_RegWrite" value="31">
					</opcode>
					<opcode name="Lock" symbol="OPCODE_Lock" value="32">
					</opcode>
					<opcode name="EventDumpIri" symbol="OPCODE_EventDumpIri" value="33">
					</opcode>
					<opcode name="EventDumpCwddepm" symbol="OPCODE_EventDumpCwddepm" value="34">
					</opcode>
					<opcode name="EventDumpPayloadInput" symbol="OPCODE_EventDumpPayloadInput" value="35">
					</opcode>
				</opcodes>
				<channels>
					<channel name="AMD-Kernel-PPLib-Provider/Analytic" chid="AMD-Kernel-PPLib-Provider/Analytic" symbol="CHANNEL_ANALYTIC" type="Analytic" enabled="false" message="$(string.AMD-Kernel-PPLib.channel.CHANNEL_PPLib_ANALYTIC.message)">
					</channel>
				</channels>
				<templates>
					<template tid="PPLog">
						<data name="Adapter" inType="win:Int32" outType="xs:int">
						</data>
						<data name="BDF" inType="win:AnsiString" outType="xs:string">
						</data>
						<data name="Severity" inType="win:AnsiString" outType="xs:string">
						</data>
						<data name="FileName" inType="win:AnsiString" outType="xs:string">
						</data>
						<data name="Line" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Function" inType="win:AnsiString" outType="xs:string">
						</data>
						<data name="Payload" inType="win:AnsiString" outType="xs:string">
						</data>
					</template>
					<template tid="EventDumpPPIri">
						<data name="serviceId" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="inputSize" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="inputBlob" inType="win:Binary" outType="xs:hexBinary" length="inputSize">
						</data>
						<data name="outputSize" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="outputBlob" inType="win:Binary" outType="xs:hexBinary" length="outputSize">
						</data>
					</template>
					<template tid="EventDumpCwddepm">
						<data name="cwddeCmdSize" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="cwddeCmdBlob" inType="win:Binary" outType="xs:hexBinary" length="cwddeCmdSize">
						</data>
						<data name="inputSize" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="inputBlob" inType="win:Binary" outType="xs:hexBinary" length="inputSize">
						</data>
						<data name="outputSize" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="outputBlob" inType="win:Binary" outType="xs:hexBinary" length="outputSize">
						</data>
					</template>
					<template tid="EventDumpPayloadInput">
						<data name="inputSize" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="inputBlob" inType="win:Binary" outType="xs:hexBinary" length="inputSize">
						</data>
					</template>
				</templates>
			</provider>
                 	<!--  ***************************** PPLib Events End*************************** -->  

               		<!--  ***************************** PowerProfiling Events ********************* -->   
			<provider name="AMD-Kernel-PowerProfiling" guid="{9C3EBC4E-22CF-442C-A564-8913B661476E}" symbol="AMD_KERNEL_PowerProfiling_GUID" resourceFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" messageFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" parameterFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys ">
				<events>
					<event symbol="PowerProfilingApu0" value="0" version="0" channel="AMD-Kernel-PowerProfiling-Provider/Analytic" level="win:Informational" task="Adapter0" opcode="APU" template="PowerProfilingApu">
					</event>
					<event symbol="PowerProfilingApu1" value="1" version="0" channel="AMD-Kernel-PowerProfiling-Provider/Analytic" level="win:Informational" task="Adapter1" opcode="APU" template="PowerProfilingApu">
					</event>
					<event symbol="PowerProfilingDgpu0" value="2" version="0" channel="AMD-Kernel-PowerProfiling-Provider/Analytic" level="win:Informational" task="Adapter0" opcode="dGPU" template="PowerProfilingDgpu">
					</event>
					<event symbol="PowerProfilingDgpu1" value="3" version="0" channel="AMD-Kernel-PowerProfiling-Provider/Analytic" level="win:Informational" task="Adapter1" opcode="dGPU" template="PowerProfilingDgpu">
					</event>
				</events>
				<levels>
				</levels>
				<tasks>
					<task name="Adapter0" symbol="TASK_ADAPTER_0" value="2" eventGUID="{B885942E-B4D7-4D42-9E52-D754108BF756}">
					</task>
					<task name="Adapter1" symbol="TASK_ADAPTER_1" value="3" eventGUID="{B241BD40-7A60-4B85-B562-F9FDD337D776}">
					</task>
				</tasks>
				<opcodes>
					<opcode name="APU" symbol="OPCODE_POWERPROFILINGAPU" value="10">
					</opcode>
					<opcode name="dGPU" symbol="OPCODE_POWERPROFILINGDGPU" value="11">
					</opcode>
				</opcodes>
				<channels>
					<channel name="AMD-Kernel-PowerProfiling-Provider/Analytic" chid="AMD-Kernel-PowerProfiling-Provider/Analytic" symbol="CHANNEL_ANALYTIC" type="Analytic" enabled="false" message="$(string.AMD-Kernel-PowerProfiling.channel.CHANNEL_PPLib_ANALYTIC.message)">
					</channel>
				</channels>
				<templates>
					<template tid="PowerProfilingApu">
						<data name="BDF 00:00:00" inType="win:HexInt32" outType="win:HexInt32">
						</data>
						<data name="DID" inType="win:HexInt32" outType="win:HexInt32">
						</data>
						<data name="Power" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Sclk" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Mclk" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Lclk" inType="win:Int32" outType="xs:int">
						</data>
						<data name="GPU Activity Percent" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Temperature" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Vclk (APU)" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Eclk (APU)" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Aclk (APU)" inType="win:Int32" outType="xs:int">
						</data>
					</template>
					<template tid="PowerProfilingDgpu">
						<data name="BDF 00:00:00" inType="win:HexInt32" outType="win:HexInt32">
						</data>
						<data name="DID" inType="win:HexInt32" outType="win:HexInt32">
						</data>
						<data name="Power" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Sclk" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Mclk" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Lclk" inType="win:Int32" outType="xs:int">
						</data>
						<data name="GPU Activity Percent" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Temperature" inType="win:Int32" outType="xs:int">
						</data>
						<data name="SamuClk (dGPU)" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Fan Speed Percent (dGPU)" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Fan RPM (dGPU)" inType="win:Int32" outType="xs:int">
						</data>
						<data name="Link Speed (dGPU)" inType="win:Int32" outType="xs:int">
						</data>
					</template>
				</templates>
			</provider>

			
               		<!--  ***************************** PowerProfiling Events End ***************** -->   
			
			<!--  ******************************* swSMU Events **************************** -->  
			<provider name="AMD-Kernel-SwSMU" guid="{402D8213-346F-4A39-98DF-73AE640019A9}" symbol="AMDKernelSwSMU" resourceFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" messageFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys" parameterFileName="%WINDIR%\SYSTEM32\drivers\amdkmdag.sys">
				<events>
					<event symbol="SwSmuGeneral" value="1" version="0" level="win:Informational" task="SwSmuLog" opcode="win:Info" template="SwSmuLog" keywords="General ">
					</event>
					<event symbol="SendMessageStart" value="2" version="0" level="win:Informational" task="SendMessage" opcode="win:Start" template="SMUSendMessageArgs" keywords="Dispatcher ">
					</event>
					<event symbol="SendMessageResponse" value="3" version="0" level="win:Informational" task="GetSMUResponse" opcode="GetSMUReponse" template="SMUSendMessageResponseArgs" keywords="Dispatcher ">
					</event>
					<event symbol="SendMessageWithParamStart" value="4" version="0" level="win:Informational" task="SendMessageWithParams" opcode="win:Start" template="SMUSendMessageWithParamArgs" keywords="Dispatcher ">
					</event>
					<event symbol="SendOverdriveTable_SMU11" value="5" version="0" level="win:Informational" task="Overdrive" opcode="SendODTable" template="SMU11_Overdrive_SettingsTable" keywords="Overdrive ">
					</event>
					<event symbol="GetOverdriveTable_SMU11" value="6" version="0" level="win:Informational" task="Overdrive" opcode="GetODTable" template="SMU11_Overdrive_SettingsTable" keywords="Overdrive ">
					</event>
					<event symbol="GetOverdriveGfxClockBaseVoltage_SMU11" value="7" version="0" level="win:Informational" task="Overdrive" opcode="win:Info" template="SMU11_Overdrive_GetGfxClockBaseVoltage" keywords="Overdrive ">
					</event>
					<event symbol="GetOverdriveFeatures_SMU11" value="8" version="0" level="win:Informational" task="Overdrive" opcode="GetODFeatures" template="SMU11_Overdrive_SettingsTable" keywords="Overdrive ">
					</event>
					<event symbol="GetPowerLimit" value="9" version="0" level="win:Informational" task="Power" opcode="GetPowerLimit" template="SMUGetPowerLimit" keywords="Power ">
					</event>
					<event symbol="EnableDisableSMUFeature" value="10" version="0" level="win:Informational" task="Dispatcher" opcode="EnableDisableSMUFeature" template="SMUEnableDisableFeature" keywords="Dispatcher ">
					</event>
					<event symbol="PowerGateBlock" value="11" version="0" level="win:Informational" task="Power" opcode="PowerGateBlock" template="SMUPowerGateBlock" keywords="Power ">
					</event>
					<event symbol="SetClockFrequency" value="12" version="0" level="win:Informational" task="DPM" opcode="SetClockFrequency" template="SetClockFrequency" keywords="DPM ">
					</event>
					<event symbol="GetClockFrequency" value="13" version="0" level="win:Informational" task="DPM" opcode="GetClockFrequency" template="GetClockFrequency" keywords="DPM ">
					</event>
					<event symbol="SetWorkloadPolicy" value="14" version="0" level="win:Informational" task="DPM" opcode="SetWorkloadPolicy" template="SetWorkloadPolicy" keywords="DPM ">
					</event>
					<event symbol="EnterBXCO" value="15" version="0" level="win:Informational" task="IPS" opcode="EnterBXCO" template="EnterBXCO" keywords="IPS ">
					</event>
					<event symbol="ExitBXCO" value="16" version="0" level="win:Informational" task="IPS" opcode="ExitBXCO" template="ExitBXCO" keywords="IPS ">
					</event>
					<event symbol="SetDriverSMUConfigTable" value="17" version="0" level="win:Informational" task="PMLog" opcode="SetDriverSMUConfigTable" template="SetDriverSMUConfigTable" keywords="PMLog ">
					</event>
					<event symbol="GetMetricsTable_SMU11" value="18" version="0" level="win:Informational" task="PMLog" opcode="GetMetricsTable" template="SMU11_PM_GetMetricsTable" keywords="PMLog ">
					</event>
					<event symbol="GetTargetOperatingTemperature" value="19" version="0" level="win:Informational" task="Temperature" opcode="GetTargetOperatingTemperature" template="GetTargetOperatingTemperature" keywords="Temperature ">
					</event>
					<event symbol="TransferTable_SMU11" value="20" version="0" level="win:Informational" task="Dispatcher" opcode="TransferTable" template="SMU11_TransferTable" keywords="Dispatcher ">
					</event>
				</events>
				<levels>
				</levels>
				<tasks>
					<task name="SwSmuLog" symbol="TASK_SwSmuLog" value="2" eventGUID="{9966DB55-3BBB-4F25-9762-0F6E46A1220D}">
					</task>
					<task name="Dispatcher" symbol="TASK_Dispatcher" value="3" eventGUID="{1DD14866-14D0-42C9-9E98-E2EE42ECBBFB}">
					</task>
					<task name="SendMessage" symbol="TASK_SendMessage" value="1" eventGUID="{155146D2-C636-4489-B2F8-20510374A2A7}">
					</task>
					<task name="SendMessageWithParams" symbol="TASK_SendMessageWithParams" value="4" eventGUID="{F7597021-AD7F-497C-B72E-DE659C30D3ED}">
					</task>
					<task name="Overdrive" symbol="TASK_Overdrive" value="5" eventGUID="{B426061C-1FC2-465C-8544-6A030E0A8225}">
					</task>
					<task name="Power" symbol="TASK_Power" value="6" eventGUID="{BC6B54F2-FF78-4E0A-A825-A1A926E16826}">
					</task>
					<task name="GetSMUResponse" symbol="SYMBOL_GetSMUResponse" value="7" eventGUID="{70ADDF47-2199-40A8-96FE-4E2B6CBA4308}">
					</task>
					<task name="DPM" symbol="TASK_DPM" value="9" eventGUID="{02B69411-7A8C-479D-A6DE-2CF1F8607A1F}">
					</task>
					<task name="GetClockFrequency" symbol="TASK_GetClockFrequency" value="8" eventGUID="{B073EEE8-15CA-42F3-A545-8EA6B1918BB6}">
					</task>
					<task name="IPS" symbol="TASK_IPS" value="10" eventGUID="{786F3EEC-9548-4985-A1C7-644B57D79F6F}">
					</task>
					<task name="PMLog" symbol="TASK_PMLog" value="11" eventGUID="{3E9E7AE9-63CF-4FEB-B329-7D69F84B4372}">
					</task>
					<task name="Temperature" symbol="TASK_Temperature" value="12" eventGUID="{72E2DC6A-479D-4CDC-8723-1967102F4765}">
					</task>
				</tasks>
				<opcodes>
					<opcode name="SwSmuGeneral" symbol="OPCODE_SwSmuGeneral" value="11">
					</opcode>
					<opcode name="SendODTable" symbol="SYMBOL_SendODTable" value="10">
					</opcode>
					<opcode name="GetODTable" symbol="SYMBOL_GetODTable" value="12">
					</opcode>
					<opcode name="GetSMUReponse" symbol="SYMBOL_GetResponseForMsg" value="13">
					</opcode>
					<opcode name="GetODFeatures" symbol="SYMBOL_GetODFeatures" value="14">
					</opcode>
					<opcode name="GetOD_GfxClockBaseVoltage" symbol="SYMBOL_GetOD_GfxClockBaseVoltage" value="15">
					</opcode>
					<opcode name="GetPowerLimit" symbol="SYMBOL_GetPowerLimit" value="16">
					</opcode>
					<opcode name="EnableDisableSMUFeature" symbol="SYMBOL_EnableDisableSMUFeature" value="17">
					</opcode>
					<opcode name="PowerGateBlock" symbol="SYMBOL_PowerGateBlock" value="18">
					</opcode>
					<opcode name="SetClockFrequency" symbol="SYMBOL_SetClockFrequency" value="19">
					</opcode>
					<opcode name="GetClockFrequency" symbol="SYMBOL_GetClockFrequency" value="20">
					</opcode>
					<opcode name="SetWorkloadPolicy" symbol="SYMBOL_SetWorkloadPolicy" value="21">
					</opcode>
					<opcode name="EnterBXCO" symbol="SYMBOL_EnterBXCO" value="22">
					</opcode>
					<opcode name="ExitBXCO" symbol="SYMBOL_ExitBXCO" value="23">
					</opcode>
					<opcode name="GetMetricsTable" symbol="SYMBOL_GetMetricsTable" value="24">
					</opcode>
					<opcode name="SetDriverSMUConfigTable" symbol="SYMBOL_SetDriverSMUConfigTable" value="25">
					</opcode>
					<opcode name="GetTargetOperatingTemperature" symbol="SYMBOL_GetTargetOperatingTemperature" value="26">
					</opcode>
					<opcode name="TransferTable" symbol="SYMBOL_TransferTable" value="27">
					</opcode>
				</opcodes>
				<channels>
					<channel name="AMD-Kernel-SwSMU-Provider/Analytic" chid="AMD-Kernel-SwSMU-Provider/Analytic" symbol="CHANNEL_ANALYTIC" type="Analytic" enabled="false">
					</channel>
				</channels>
				<keywords>
					<keyword name="Dispatcher" symbol="SYMBOL_Dispatcher" mask="0x1">
					</keyword>
					<keyword name="General" symbol="SYMBOL_General" mask="0x800000000000">
					</keyword>
					<keyword name="Overdrive" symbol="SYMBOL_Overdrive" mask="0x2">
					</keyword>
					<keyword name="Power" symbol="SYMBOL_Power" mask="0x4">
					</keyword>
					<keyword name="DPM" symbol="SYMBOL_DPM" mask="0x8">
					</keyword>
					<keyword name="IPS" symbol="SYMBOL_IPS" mask="0x10">
					</keyword>
					<keyword name="PMLog" symbol="SYMBOL_PMLog" mask="0x20">
					</keyword>
					<keyword name="Temperature" symbol="SYMBOL_Temperature" mask="0x40">
					</keyword>
				</keywords>
				<maps>
					<valueMap name="SMU11_GetDPMFrequencyType">
						<map value="30" message="$(string.AMD-Kernel-SwSMU.map.GetDPMFrequencyTypeNV10.30.message)">
						</map>
						<map value="40" message="$(string.AMD-Kernel-SwSMU.map.GetDPMFrequencyTypeNV10.40.message)">
						</map>
						<map value="31" message="$(string.AMD-Kernel-SwSMU.map.GetDPMFrequencyTypeNV10.31.message)">
						</map>
					</valueMap>
					<valueMap name="PowerGateBlock">
						<map value="0" message="$(string.AMD-Kernel-SwSMU.map.PowerGateBlock.0.message)">
						</map>
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.PowerGateBlock.1.message)">
						</map>
					</valueMap>
					<valueMap name="PowerGate">
						<map value="0" message="$(string.AMD-Kernel-SwSMU.map.PowerGate.0.message)">
						</map>
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.PowerGate.1.message)">
						</map>
					</valueMap>
					<valueMap name="SMU11_ProcessResponse">
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.1.message)">
						</map>
						<map value="255" message="$(string.AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.255.message)">
						</map>
						<map value="254" message="$(string.AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.254.message)">
						</map>
						<map value="253" message="$(string.AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.253.message)">
						</map>
						<map value="252" message="$(string.AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.252.message)">
						</map>
					</valueMap>
					<valueMap name="SMU11_SMUMessage">
						<map value="26" message="$(string.AMD-Kernel-SwSMU.map.SMUMessage.26.message)">
						</map>
						<map value="27" message="$(string.AMD-Kernel-SwSMU.map.SMUMessage.27.message)">
						</map>
						<map value="28" message="$(string.AMD-Kernel-SwSMU.map.SMUMessage.28.message)">
						</map>
						<map value="29" message="$(string.AMD-Kernel-SwSMU.map.SMUMessage.29.message)">
						</map>
						<map value="30" message="$(string.AMD-Kernel-SwSMU.map.SMUMessage.30.message)">
						</map>
						<map value="31" message="$(string.AMD-Kernel-SwSMU.map.SMUMessage.31.message)">
						</map>
						<map value="32" message="$(string.AMD-Kernel-SwSMU.map.SMUMessage.32.message)">
						</map>
						<map value="4" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.4.message)">
						</map>
						<map value="5" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.5.message)">
						</map>
						<map value="6" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.6.message)">
						</map>
						<map value="7" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.7.message)">
						</map>
						<map value="8" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.8.message)">
						</map>
						<map value="9" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.9.message)">
						</map>
						<map value="10" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.10.message)">
						</map>
						<map value="11" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.11.message)">
						</map>
						<map value="12" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.12.message)">
						</map>
						<map value="13" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.13.message)">
						</map>
						<map value="14" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.14.message)">
						</map>
						<map value="15" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.15.message)">
						</map>
						<map value="16" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.16.message)">
						</map>
						<map value="17" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.17.message)">
						</map>
						<map value="18" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.18.message)">
						</map>
						<map value="19" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.19.message)">
						</map>
						<map value="20" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.20.message)">
						</map>
						<map value="21" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.21.message)">
						</map>
						<map value="22" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.22.message)">
						</map>
						<map value="23" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.23.message)">
						</map>
						<map value="24" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.24.message)">
						</map>
						<map value="25" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.25.message)">
						</map>
						<map value="70" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.70.message)">
						</map>
						<map value="72" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.72.message)">
						</map>
						<map value="33" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.33.message)">
						</map>
						<map value="34" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.34.message)">
						</map>
						<map value="36" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.36.message)">
						</map>
						<map value="37" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.37.message)">
						</map>
						<map value="38" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.38.message)">
						</map>
						<map value="39" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.39.message)">
						</map>
						<map value="40" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.40.message)">
						</map>
						<map value="41" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.41.message)">
						</map>
						<map value="42" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.42.message)">
						</map>
						<map value="43" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.43.message)">
						</map>
						<map value="44" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.44.message)">
						</map>
						<map value="45" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.45.message)">
						</map>
						<map value="46" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.46.message)">
						</map>
						<map value="50" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.50.message)">
						</map>
						<map value="51" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.51.message)">
						</map>
						<map value="52" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.52.message)">
						</map>
						<map value="53" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.53.message)">
						</map>
						<map value="54" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.54.message)">
						</map>
						<map value="55" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.55.message)">
						</map>
						<map value="56" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.56.message)">
						</map>
						<map value="58" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.58.message)">
						</map>
						<map value="59" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.59.message)">
						</map>
						<map value="60" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.60.message)">
						</map>
						<map value="61" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.61.message)">
						</map>
						<map value="62" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.62.message)">
						</map>
						<map value="63" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.63.message)">
						</map>
						<map value="64" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.64.message)">
						</map>
						<map value="65" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.65.message)">
						</map>
						<map value="66" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.66.message)">
						</map>
						<map value="67" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.67.message)">
						</map>
						<map value="68" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.68.message)">
						</map>
						<map value="69" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.69.message)">
						</map>
						<map value="71" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.71.message)">
						</map>
						<map value="73" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.73.message)">
						</map>
						<map value="74" message="$(string.AMD-Kernel-SwSMU.map.SMUMessageNV10.74.message)">
						</map>
					</valueMap>
					<valueMap name="ClockTypes_BGD">
						<map value="0" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.0.message)">
						</map>
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.1.message)">
						</map>
						<map value="2" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.2.message)">
						</map>
						<map value="3" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.3.message)">
						</map>
						<map value="4" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.4.message)">
						</map>
						<map value="5" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.5.message)">
						</map>
						<map value="6" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.6.message)">
						</map>
						<map value="7" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.7.message)">
						</map>
						<map value="8" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.8.message)">
						</map>
						<map value="9" message="$(string.AMD-Kernel-SwSMU.map.ClockTypes_BGD.9.message)">
						</map>
					</valueMap>
					<valueMap name="ClockLimitType">
						<map value="0" message="$(string.AMD-Kernel-SwSMU.map.ClockLimitType.0.message)">
						</map>
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.ClockLimitType.1.message)">
						</map>
						<map value="2" message="$(string.AMD-Kernel-SwSMU.map.ClockLimitType.2.message)">
						</map>
						<map value="3" message="$(string.AMD-Kernel-SwSMU.map.ClockLimitType.3.message)">
						</map>
					</valueMap>
					<valueMap name="WorkloadMask">
						<map value="0" message="$(string.AMD-Kernel-SwSMU.map.WorkloadMask.0.message)">
						</map>
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.WorkloadMask.1.message)">
						</map>
						<map value="2" message="$(string.AMD-Kernel-SwSMU.map.WorkloadMask.2.message)">
						</map>
						<map value="3" message="$(string.AMD-Kernel-SwSMU.map.WorkloadMask.3.message)">
						</map>
						<map value="4" message="$(string.AMD-Kernel-SwSMU.map.WorkloadMask.4.message)">
						</map>
						<map value="5" message="$(string.AMD-Kernel-SwSMU.map.WorkloadMask.5.message)">
						</map>
						<map value="6" message="$(string.AMD-Kernel-SwSMU.map.WorkloadMask.6.message)">
						</map>
					</valueMap>
					<valueMap name="IpsCommands">
						<map value="0" message="$(string.AMD-Kernel-SwSMU.map.IpsCommands.0.message)">
						</map>
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.IpsCommands.1.message)">
						</map>
						<map value="2" message="$(string.AMD-Kernel-SwSMU.map.IpsCommands.2.message)">
						</map>
						<map value="3" message="$(string.AMD-Kernel-SwSMU.map.IpsCommands.3.message)">
						</map>
						<map value="4" message="$(string.AMD-Kernel-SwSMU.map.IpsCommands.4.message)">
						</map>
						<map value="5" message="$(string.AMD-Kernel-SwSMU.map.IpsCommands.5.message)">
						</map>
					</valueMap>
					<valueMap name="SMU11_TableId">
						<map value="0" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.0.message)">
						</map>
						<map value="1" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.1.message)">
						</map>
						<map value="2" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.2.message)">
						</map>
						<map value="3" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.3.message)">
						</map>
						<map value="4" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.4.message)">
						</map>
						<map value="5" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.5.message)">
						</map>
						<map value="6" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.6.message)">
						</map>
						<map value="7" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.7.message)">
						</map>
						<map value="8" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.8.message)">
						</map>
						<map value="9" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.9.message)">
						</map>
						<map value="10" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.10.message)">
						</map>
						<map value="11" message="$(string.AMD-Kernel-SwSMU.map.SMU11_TableId.11.message)">
						</map>
					</valueMap>
				</maps>
				<templates>
					<template tid="SMUSendMessageArgs">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="Message" inType="win:UInt32" map="SMU11_SMUMessage">
						</data>
					</template>
					<template tid="SwSmuLog">
						<data name="payload" inType="win:AnsiString" outType="xs:string">
						</data>
					</template>
					<template tid="SMUSendMessageWithParamArgs">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="Message" inType="win:UInt32" map="SMU11_SMUMessage">
						</data>
						<data name="Param" inType="win:HexInt32" outType="win:HexInt32">
						</data>
					</template>
					<template tid="SMUSendMessageResponseArgs">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="response" inType="win:UInt32" map="SMU11_ProcessResponse">
						</data>
					</template>
					<template tid="SMU11_Overdrive_SettingsTable">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="ODTableCount" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="ODTableArray" inType="win:UInt32" outType="xs:unsignedInt" count="ODTableCount">
						</data>
					</template>
					<template tid="SMU11_Overdrive_GetGfxClockBaseVoltage">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="frequency" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="voltage" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="SMUGetPowerLimit">
						<data name="pSMu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="powerLimit" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="SMUEnableDisableFeature">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="enableFlag" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="featureMask" inType="win:UInt64" outType="xs:unsignedLong">
						</data>
					</template>
					<template tid="SMUPowerGateBlock">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="powerGate" inType="win:UInt32" map="PowerGate">
						</data>
						<data name="block" inType="win:UInt32" map="PowerGateBlock">
						</data>
						<data name="enableDynamicPG" inType="win:UInt8" outType="xs:unsignedByte">
						</data>
					</template>
					<template tid="SetClockFrequency">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="clockType" inType="win:UInt32" map="ClockTypes_BGD">
						</data>
						<data name="clockLimitType" inType="win:UInt32" map="ClockLimitType">
						</data>
						<data name="clockValue" inType="win:UInt64" outType="xs:unsignedLong">
						</data>
					</template>
					<template tid="GetClockFrequency">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="clockType" inType="win:UInt32" map="ClockTypes_BGD">
						</data>
						<data name="dpmFrequencyType" inType="win:UInt32" map="SMU11_GetDPMFrequencyType">
						</data>
						<data name="clockFrequency" inType="win:UInt64" outType="xs:unsignedLong">
						</data>
					</template>
					<template tid="SetWorkloadPolicy">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="workloadMask" inType="win:UInt32" map="WorkloadMask">
						</data>
					</template>
					<template tid="EnterBXCO">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="command" inType="win:UInt32" map="IpsCommands">
						</data>
					</template>
					<template tid="ExitBXCO">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="command" inType="win:UInt32" map="IpsCommands">
						</data>
					</template>
					<template tid="SMU11_PM_GetMetricsTable">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="metricsTableCount" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="metricsTable" inType="win:UInt32" outType="xs:unsignedInt" count="metricsTableCount">
						</data>
					</template>
					<template tid="SetDriverSMUConfigTable">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="gfxClk_averageTau" inType="win:UInt16" outType="xs:unsignedShort">
						</data>
						<data name="socClk_averageTau" inType="win:UInt16" outType="xs:unsignedShort">
						</data>
						<data name="uClk_averageTau" inType="win:UInt16" outType="xs:unsignedShort">
						</data>
						<data name="gfx_activity_averageTau" inType="win:UInt16" outType="xs:unsignedShort">
						</data>
						<data name="mem_activity_averageTau" inType="win:UInt16" outType="xs:unsignedShort">
						</data>
						<data name="socket_power_averageTau" inType="win:UInt16" outType="xs:unsignedShort">
						</data>
					</template>
					<template tid="GetTargetOperatingTemperature">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="targetOperatingTemperature" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="defaultOperatingTemperature" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="minOperatingTemperature" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="maxOperatingTemperature" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="stepOperatingTemperature" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="hotspotOperatingTemperature" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
					<template tid="SMU11_TransferTable">
						<data name="pSmu" inType="win:Pointer" outType="win:HexInt64">
						</data>
						<data name="bus" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="device" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
						<data name="tableId" inType="win:UInt32" outType="xs:unsignedInt">
						</data>
					</template>
				</templates>
			</provider>
			
			<!--  ******************************* swSMU Events End *********************** --> 
		</events>
	</instrumentation>
	<localization>
		<resources culture="en-US">
			<stringTable>
				<string id="opcode.Stop" value="Stop">
				</string>
				<string id="opcode.Start" value="Start">
				</string>
				<string id="opcode.Send" value="Send">
				</string>
				<string id="opcode.Info" value="Info">
				</string>
				<string id="level.Informational" value="Information">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.Vsync.message" value="TurboSync Vsync">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.TurboSyncFlipRetryAtPassive.message" value="TurboSync Retry Flip at Passive Level">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.TurboSyncFlipQueueWorkItemToRetry.message" value="TurboSync Flip Failed Queue WorkItem to Retry">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.TimerNodeTimeout.message" value="TurboSync Timer Node Timeout">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.TimerNodeSkip.message" value="TurboSync Timer Node Skip">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.TimerNodeRelease.message" value="TurboSync Timer Node Release">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.TimerNodeHeld.message" value="TurboSync Timer Node Held">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.FlipVsync.message" value="TurboSync Flip Vsync">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.FlipImmediate.message" value="TurboSync Flip Immediate">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.CopyStart.message" value="TurboSync Copy Start">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.CopyEnd.message" value="TurboSync Copy End">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.CheckFreeSyncActive.message" value="TurboSync Check FreeSync Active">
				</string>
				<string id="AMD-Kernel.event.TurboSyncEventMap.AverageFrameTime.message" value="TurboSync Average Frame Time">
				</string>
				<string id="AMD-Kernel.event.TurboSync.message" value="TurboSync Event">
				</string>
				<string id="AMD-Kernel.event.GfxQueueScheduler.WorkItemCbExit.message" value="WorkItem Callback Exit">
				</string>
				<string id="AMD-Kernel.event.GfxQueueScheduler.WorkItemCbEnter.message" value="WorkItem Callback Enter">
				</string>
				<string id="AMD-Kernel.event.GfxQueueScheduler.ToLow.message" value="Gfx Queue Switch To Low">
				</string>
				<string id="AMD-Kernel.event.GfxQueueScheduler.ToHigh.message" value="Gfx Queue Switch To High">
				</string>
				<string id="AMD-Kernel.event.GfxQueueScheduler.QueueWorkItem.message" value="Queueing WorkItem">
				</string>
				<string id="AMD-Kernel.event.GfxQueueScheduler.OsPreemption.message" value="Submitting Os Preemption">
				</string>
				<string id="AMD-Kernel.event.3.message" value="Gfx Queue Scheduler Event">
				</string>
				<string id="AMD-Kernel.event.2.message" value="Switching Gfx Queue">
				</string>
				<string id="AMD-Kernel.event.1.message" value="VSync Type %2 VidPnTargetId %2">
				</string>
				<string id="AMD-Kernel.event.0.message" value="Sync VidPnTargetId %1 hAllocation %2 PrimaryPhysicalAddress %3">
				</string>
				<string id="AMD-Kernel.channel.CHANNEL_ANALYTIC.message" value="Events for analysis of swap chain timing.">
				</string>
				<string id="AMD-Kernel-SwSMU.task.TASK_SendMessage.message" value="Send msg to SMU">
				</string>
				<string id="AMD-Kernel-SwSMU.map.WorkloadMask.6.message" value="Custom">
				</string>
				<string id="AMD-Kernel-SwSMU.map.WorkloadMask.5.message" value="Compute">
				</string>
				<string id="AMD-Kernel-SwSMU.map.WorkloadMask.4.message" value="VR">
				</string>
				<string id="AMD-Kernel-SwSMU.map.WorkloadMask.3.message" value="Video">
				</string>
				<string id="AMD-Kernel-SwSMU.map.WorkloadMask.2.message" value="PowerSaving">
				</string>
				<string id="AMD-Kernel-SwSMU.map.WorkloadMask.1.message" value="Fullscreen3D">
				</string>
				<string id="AMD-Kernel-SwSMU.map.WorkloadMask.0.message" value="Default">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.255.message" value="Result_Failed">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.254.message" value="Result_Unknown_Cmd">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.253.message" value="Result_Rejected_Prereq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.252.message" value="Result_Rejected_Busy">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUProcessResponseNV10.1.message" value="Result_OK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.9.message" value="PPSMC_MSG_EnableSmuFeaturesHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.8.message" value="PPSMC_MSG_EnableSmuFeaturesLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.74.message" value="PPSMC_MSG_DALEnableDummyPstateChange">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.73.message" value="PPSMC_MSG_DALDisableDummyPstateChange">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.72.message" value="PPSMC_MSG_BacoAudioD3PME">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.71.message" value="PPSMC_MSG_SetTemperatureInputSelect">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.70.message" value="PPSMC_MSG_ArmD3">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.7.message" value="PPSMC_MSG_DisableAllSmuFeatures">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.69.message" value="PPSMC_MSG_GetVoltageByDpmOverdrive">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.68.message" value="PPSMC_MSG_SetGeminiApertureLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.67.message" value="PPSMC_MSG_SetGeminiApertureHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.66.message" value="PPSMC_MSG_SetGeminiMode">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.65.message" value="PPSMC_MSG_SetMemoryChannelConfig">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.64.message" value="PPSMC_MSG_NumOfDisplays">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.63.message" value="PPSMC_MSG_ConfigureGfxDidt">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.62.message" value="PPSMC_MSG_GetDebugData">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.61.message" value="PPSMC_MSG_DramLogSetDramSize">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.60.message" value="PPSMC_MSG_DramLogSetDramAddrLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.6.message" value="PPSMC_MSG_EnableAllSmuFeatures">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.59.message" value="PPSMC_MSG_DramLogSetDramAddrHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.58.message" value="PPSMC_MSG_RunBtc">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.56.message" value="PPSMC_MSG_NotifyPowerSource">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.55.message" value="PPSMC_MSG_ReenableAcDcInterrupt">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.54.message" value="PPSMC_MSG_GetPptLimit">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.53.message" value="PPSMC_MSG_SetPptLimit">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.52.message" value="PPSMC_MSG_PrepareMp1ForShutdown">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.51.message" value="PPSMC_MSG_PrepareMp1ForReset">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.50.message" value="PPSMC_MSG_PrepareMp1ForUnload">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.5.message" value="PPSMC_MSG_SetAllowedFeaturesMaskHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.46.message" value="PPSMC_MSG_PowerDownJpeg">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.45.message" value="PPSMC_MSG_PowerUpJpeg">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.44.message" value="PPSMC_MSG_PowerDownVcn">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.43.message" value="PPSMC_MSG_PowerUpVcn">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.42.message" value="PPSMC_MSG_DisallowGfxOff">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.41.message" value="PPSMC_MSG_AllowGfxOff">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.40.message" value="PPSMC_MSG_GetDcModeMaxDpmFreq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.4.message" value="PPSMC_MSG_SetAllowedFeaturesMaskLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.39.message" value="PPSMC_MSG_SetVideoFps">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.38.message" value="PPSMC_MSG_GetVoltageByDpm">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.37.message" value="PPSMC_MSG_SetUclkFastSwitch">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.36.message" value="PPSMC_MSG_SetWorkloadMask">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.34.message" value="PPSMC_MSG_SetMinDeepSleepDcefclk">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.33.message" value="PPSMC_MSG_OverridePcieParameters">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.25.message" value="PPSMC_MSG_ExitBaco">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.24.message" value="PPSMC_MSG_EnterBaco">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.23.message" value="PPSMC_MSG_SetSystemVirtualDramAddrLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.22.message" value="PPSMC_MSG_SetSystemVirtualDramAddrHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.21.message" value="PPSMC_MSG_UseBackupPPTable">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.20.message" value="PPSMC_MSG_UseDefaultPPTable">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.19.message" value="PPSMC_MSG_TransferTableDram2Smu">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.18.message" value="PPSMC_MSG_TransferTableSmu2Dram">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.17.message" value="PPSMC_MSG_SetToolsDramAddrLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.16.message" value="PPSMC_MSG_SetToolsDramAddrHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.15.message" value="PPSMC_MSG_SetDriverDramAddrLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.14.message" value="PPSMC_MSG_SetDriverDramAddrHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.13.message" value="PPSMC_MSG_GetEnabledSmuFeaturesHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.12.message" value="PPSMC_MSG_GetEnabledSmuFeaturesLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.11.message" value="PPSMC_MSG_DisableSmuFeaturesHigh">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessageNV10.10.message" value="PPSMC_MSG_DisableSmuFeaturesLow">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessage.32.message" value="PPSMC_MSG_GetDpmFreqByIndex">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessage.31.message" value="PPSMC_MSG_GetMaxDpmFreq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessage.30.message" value="PPSMC_MSG_GetMinDpmFreq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessage.29.message" value="PPSMC_MSG_SetHardMaxByFreq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessage.28.message" value="PPSMC_MSG_SetHardMinByFreq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessage.27.message" value="PPSMC_MSG_SetSoftMaxByFreq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMUMessage.26.message" value="PPSMC_MSG_SetSoftMinByFreq">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.9.message" value="OVERDRIVE">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.8.message" value="ACTIVITY_MONITOR_COEFF">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.7.message" value="DRIVER_SMU_CONFIG">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.6.message" value="SMU_METRICS">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.5.message" value="PMSTATUSLOG">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.4.message" value="AVGS_FUSE_OVERRIDE">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.3.message" value="AVFS_PSM_DEBUG">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.2.message" value="AVFS">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.11.message" value="PACE">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.10.message" value="I2C_COMMANDS">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.1.message" value="WATERMARKS">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_TableId.0.message" value="PPTABLE">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_OD_Settings_ID.5.message" value="GFXCLK_CURVE_VOLTAGE2">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_OD_Settings_ID.4.message" value="GFXCLK_CURVE_FREQ2">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_OD_Settings_ID.3.message" value="GFXCLK_CURVE_VOLTAGE1">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_OD_Settings_ID.2.message" value="GFXCLK_CURVE_FREQ1">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_OD_Settings_ID.1.message" value="GFXCLK_FMIN">
				</string>
				<string id="AMD-Kernel-SwSMU.map.SMU11_OD_Settings_ID.0.message" value="GFXCLK_FMAX">
				</string>
				<string id="AMD-Kernel-SwSMU.map.PowerGateBlock.1.message" value="JPEG">
				</string>
				<string id="AMD-Kernel-SwSMU.map.PowerGateBlock.0.message" value="VCN">
				</string>
				<string id="AMD-Kernel-SwSMU.map.PowerGate.1.message" value="Power_Up">
				</string>
				<string id="AMD-Kernel-SwSMU.map.PowerGate.0.message" value="Power_Down">
				</string>
				<string id="AMD-Kernel-SwSMU.map.IpsCommands.5.message" value="Exit_BOMACO">
				</string>
				<string id="AMD-Kernel-SwSMU.map.IpsCommands.4.message" value="Enter_BOMACO">
				</string>
				<string id="AMD-Kernel-SwSMU.map.IpsCommands.3.message" value="EXIT_BAMACO">
				</string>
				<string id="AMD-Kernel-SwSMU.map.IpsCommands.2.message" value="Enter_BAMACO">
				</string>
				<string id="AMD-Kernel-SwSMU.map.IpsCommands.1.message" value="Exit_BACO">
				</string>
				<string id="AMD-Kernel-SwSMU.map.IpsCommands.0.message" value="Enter_BACO">
				</string>
				<string id="AMD-Kernel-SwSMU.map.GetDPMFrequencyTypeNV10.40.message" value="GET_DC_MODE_MAX_DPM_FREQ">
				</string>
				<string id="AMD-Kernel-SwSMU.map.GetDPMFrequencyTypeNV10.31.message" value="GET_MAX_DPM_FREQ">
				</string>
				<string id="AMD-Kernel-SwSMU.map.GetDPMFrequencyTypeNV10.30.message" value="GET_MIN_DPM_FREQ">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.9.message" value="PHYCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.8.message" value="PIXCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.7.message" value="DISPCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.6.message" value="DCEFCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.5.message" value="ECLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.4.message" value="DCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.3.message" value="VCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.2.message" value="SOCCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.1.message" value="UMCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockTypes_BGD.0.message" value="GFXCLK">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockLimitType.3.message" value="Hard_Max">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockLimitType.2.message" value="Hard_Min">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockLimitType.1.message" value="Soft_Max">
				</string>
				<string id="AMD-Kernel-SwSMU.map.ClockLimitType.0.message" value="Soft_Min">
				</string>
				<string id="AMD-Kernel-PowerProfiling.channel.CHANNEL_PPLib_ANALYTIC.message" value="PowerProfiling events.">
				</string>
				<string id="AMD-Kernel-PPLib.channel.CHANNEL_PPLib_ANALYTIC.message" value="PPLib events.">
				</string>
			</stringTable>
		</resources>
	</localization>
</instrumentationManifest>
