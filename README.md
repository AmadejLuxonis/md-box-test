# M8 Controller Box Test Example

This is an example showing how to run an OAK app that controls the **M8 Controller Box** directly from an **OAK4** device.

> **Note:** This example works only on OAK4 in standalone mode. It is not supported in host-driven peripheral mode because the M8 Controller Box is connected directly to the OAK4 device.

## Usage

Running this example requires an OAK4 device with the M8 Controller Box attached.

## Standalone Mode (RVC4 only)

Install `oakctl` by following the instructions [here](https://docs.luxonis.com/software-v3/oak-apps/oakctl).

Then run the example from this directory:

```bash
oakctl connect <DEVICE_IP>
oakctl app run .
```

This builds the app from the local `oakapp.toml`, deploys it to the OAK4 device, and starts it in standalone mode.

## Peripheral Mode

This mode is not supported for this example. The M8 Controller Box must be attached directly to the OAK4 device running the app.
