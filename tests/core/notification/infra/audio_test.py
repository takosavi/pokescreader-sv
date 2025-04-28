from unittest.mock import Mock, NonCallableMock, sentinel

from pytest import fixture, mark, raises
from pytest_mock import MockerFixture

from pkscrd.core.notification.infra.audio import (
    DataType,
    DefaultDeviceNotFoundError,
    Device,
    DeviceNotFoundError,
    HostApi,
    HostApiNotFoundError,
    list_outputs,
    select_output_device,
)


def test_list_outputs(mocker: MockerFixture):
    query_hostapis = mocker.patch("sounddevice.query_hostapis")
    query_hostapis.return_value = (
        {"name": "DirectSound", "devices": [0, 1], "default_output_device": 1},
        {"name": "NoOutputDevices", "devices": [2], "default_output_device": 2},
    )

    devices = [
        {
            "index": 0,
            "name": "foo",
            "max_output_channels": 0,
            "default_samplerate": 44100.0,
        },
        {
            "index": 1,
            "name": "foo",
            "max_output_channels": 1,
            "default_samplerate": 44100.0,
        },
        {
            "index": 2,
            "name": "bar",
            "max_output_channels": 0,
            "default_samplerate": 44100.0,
        },
        {
            "index": 3,
            "name": "no host api",
            "max_output_channels": 2,
            "default_samplerate": 44100.0,
        },
    ]
    query_devices = mocker.patch("sounddevice.query_devices")
    query_devices.side_effect = lambda i: devices[i]

    outputs = list_outputs()

    assert next(outputs) == HostApi(
        name="DirectSound",
        devices=[
            Device(
                index=1,
                name="foo",
                max_channels=1,
                default_sample_rate=44100,
            ),
        ],
        default_device_index=1,
    )
    with raises(StopIteration):
        next(outputs)


class TestHostApi:

    class Test_default_output:

        def test_returns_the_device_when_given_an_existing_index(self):
            host_api = HostApi(
                name="xxx",
                devices=[
                    Device(
                        index=1,
                        name="foo",
                        max_channels=1,
                        default_sample_rate=44100,
                    )
                ],
                default_device_index=1,
            )
            assert host_api.default_device.index == 1

        def test_returns_None_when_given_a_not_existing_index(self):
            host_api = HostApi(
                name="xxx",
                devices=[],
                default_device_index=1,
            )
            assert host_api.default_device is None


class Test_select_device:

    @fixture
    def list_outputs_mock(self, mocker: MockerFixture) -> Mock:
        return mocker.patch("pkscrd.core.notification.infra.audio.list_outputs")

    class Test_given_no_host_api_name:

        class Test_given_no_device_name:

            def test_raises_DefaultDeviceNotFoundError_when_given_no_default_device(
                self,
                list_outputs_mock: Mock,
            ):
                host_api = NonCallableMock(HostApi, default_device=None)
                list_outputs_mock.return_value = iter([host_api])

                with raises(DefaultDeviceNotFoundError):
                    select_output_device()

            def test_returns_the_default_device_when_given_a_default_device(
                self,
                list_outputs_mock: Mock,
            ):
                host_api = NonCallableMock(HostApi, default_device=sentinel.expected)
                list_outputs_mock.return_value = iter([host_api])

                assert select_output_device() is sentinel.expected

        class Test_given_device_name:

            def test_raises_DeviceNotFoundError_when_the_device_name_does_not_match(
                self,
                list_outputs_mock: Mock,
            ):
                bad = NonCallableMock(Device)
                bad.name = "xxx"
                host_api = NonCallableMock(HostApi, devices=[bad])
                list_outputs_mock.return_value = iter([host_api])

                with raises(DeviceNotFoundError):
                    select_output_device(device_name="bar")

            def test_returns_the_device_when_the_device_name_matches(
                self,
                list_outputs_mock: Mock,
            ):
                expected = NonCallableMock(Device)
                expected.name = "bar"
                host_api = NonCallableMock(HostApi)
                host_api.devices = [expected]
                list_outputs_mock.return_value = iter([host_api])

                assert select_output_device(device_name="bar") is expected

    class Test_given_host_api_name:

        def test_raises_HostApiNotFoundError_when_the_host_api_name_does_not_match(
            self,
            list_outputs_mock: Mock,
        ):
            bad = NonCallableMock(HostApi)
            bad.name = "xxx"
            list_outputs_mock.return_value = iter([bad])
            with raises(HostApiNotFoundError):
                select_output_device("foo")

        class Test_given_no_device_name:

            def test_raises_DefaultDeviceNotFoundError_when_given_no_default_device(
                self,
                list_outputs_mock: Mock,
            ):
                host_api = NonCallableMock(HostApi, default_device=None)
                host_api.name = "foo"
                list_outputs_mock.return_value = iter([host_api])

                with raises(DefaultDeviceNotFoundError):
                    select_output_device("foo")

            def test_returns_the_default_device_when_given_a_default_device(
                self,
                list_outputs_mock: Mock,
            ):
                host_api = NonCallableMock(HostApi, default_device=sentinel.expected)
                host_api.name = "foo"
                list_outputs_mock.return_value = iter([host_api])

                assert select_output_device("foo") is sentinel.expected

        class Test_given_a_device_name:

            def test_raises_DeviceNotFoundError_when_the_device_name_does_not_match(
                self,
                list_outputs_mock: Mock,
            ):
                bad = NonCallableMock(Device)
                bad.name = "xxx"
                host_api = NonCallableMock(HostApi, devices=[bad])
                host_api.name = "foo"
                list_outputs_mock.return_value = iter([host_api])

                with raises(DeviceNotFoundError):
                    select_output_device("foo", "bar")

            def test_returns_the_device_when_the_device_name_matches(
                self,
                list_outputs_mock: Mock,
            ):
                expected = NonCallableMock(Device)
                expected.name = "bar"
                host_api = NonCallableMock(HostApi, devices=[expected])
                host_api.name = "foo"
                list_outputs_mock.return_value = iter([host_api])

                assert select_output_device("foo", "bar") is expected


class TestDataType:

    class Test_from_wav_sample_width:

        @mark.parametrize(
            ("value", "expected"),
            (
                (1, DataType.INT8),
                (2, DataType.INT16),
                (3, DataType.INT24),
                (4, DataType.FLOAT32),
            ),
        )
        def test_returns_successfully_when_given_an_integer_from_1_to_4(
            self,
            value: int,
            expected: DataType,
        ):
            assert DataType.from_wav_sample_width(value) is expected

        def test_raises_ValueError_when_given_another_integer(self):
            with raises(ValueError):
                DataType.from_wav_sample_width(0)
