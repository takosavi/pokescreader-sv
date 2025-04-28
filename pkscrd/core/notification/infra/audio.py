import contextlib
import dataclasses
import enum
from typing import Iterator, Optional
from wave import Wave_read

import sounddevice


@dataclasses.dataclass(frozen=True)
class Device:
    index: int
    name: str
    max_channels: int
    default_sample_rate: int


@dataclasses.dataclass
class HostApi:
    name: str
    devices: list[Device]
    default_device_index: int

    @property
    def default_device(self) -> Optional["Device"]:
        return next(
            (d for d in self.devices if d.index == self.default_device_index),
            None,
        )


def list_outputs() -> Iterator[HostApi]:
    return (
        HostApi(
            name=hostapi["name"],
            devices=devices,
            default_device_index=hostapi["default_output_device"],
        )
        for hostapi in sounddevice.query_hostapis()
        if (
            devices := [
                Device(
                    index=device["index"],
                    name=device["name"],
                    max_channels=max_channels,
                    default_sample_rate=device["default_samplerate"],
                )
                for device in (
                    sounddevice.query_devices(index) for index in hostapi["devices"]
                )
                if (max_channels := device["max_output_channels"]) > 0
            ]
        )
    )


class HostApiNotFoundError(RuntimeError): ...


class DefaultDeviceNotFoundError(RuntimeError): ...


class DeviceNotFoundError(RuntimeError): ...


def select_output_device(
    host_api_name: Optional[str] = None,
    device_name: Optional[str] = None,
) -> Device:
    if not host_api_name:
        if not device_name:
            host_api = next(
                (item for item in list_outputs() if item.default_device), None
            )
            if not host_api:
                raise DefaultDeviceNotFoundError()
            default_device = host_api.default_device
            assert default_device
            return default_device

        device = next(
            (
                device
                for host_api in list_outputs()
                for device in host_api.devices
                if device.name == device_name
            ),
            None,
        )
        if not device:
            raise DeviceNotFoundError()
        return device

    host_api = next(
        (item for item in list_outputs() if item.name == host_api_name),
        None,
    )
    if not host_api:
        raise HostApiNotFoundError()

    if not device_name:
        if not host_api.default_device:
            raise DefaultDeviceNotFoundError()
        return host_api.default_device

    device = next((item for item in host_api.devices if item.name == device_name), None)
    if not device:
        raise DeviceNotFoundError()
    return device


class DataType(enum.StrEnum):
    INT8 = "int8"
    INT16 = "int16"
    INT24 = "int24"
    FLOAT32 = "float32"

    @staticmethod
    def from_wav_sample_width(value: int) -> "DataType":
        """
        WAV サンプル幅からデータ種別を取得する.
        """
        result = _SAMPLING_WIDTHS.get(value)
        if not result:
            raise ValueError(f"Invalid sample width: {value}")
        return result


class AudioClient:

    def __init__(self, stream: sounddevice.RawOutputStream):
        self._stream = stream

    def play(self, data: bytes) -> None:
        self._stream.write(data)

    @staticmethod
    @contextlib.contextmanager
    def for_wave(wav: Wave_read, device_index: int) -> Iterator["AudioClient"]:
        with sounddevice.RawOutputStream(
            channels=wav.getnchannels(),
            samplerate=wav.getframerate(),
            dtype=DataType.from_wav_sample_width(wav.getsampwidth()),
            device=device_index,
        ) as stream:
            yield AudioClient(stream)


_SAMPLING_WIDTHS: dict[int, DataType] = {
    1: DataType.INT8,
    2: DataType.INT16,
    3: DataType.INT24,
    4: DataType.FLOAT32,
}


def main() -> None:  # pragma: no cover
    """
    デバイス一覧を表示する.
    """
    from loguru import logger

    for hostapi in list_outputs():
        logger.info("HostAPI: {}", hostapi.name)
        for device in hostapi.devices:
            logger.info("Device: {}", device)


if __name__ == "__main__":  # pragma: no cover
    main()
