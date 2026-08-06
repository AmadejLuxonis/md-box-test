#ifndef _INTERFACE_GPIO_H
#define _INTERFACE_GPIO_H

#include "PicoInterfacesBoard.h"
#include "BaseInterface.h"
#include "pico/sync.h"

#if defined(PCA9555_0_ENABLED) || defined(PCA9555_1_ENABLED)
#include "pca9555.h"
#endif

class Gpio : public BaseInterface {
public:
    Gpio();
    virtual ~Gpio();

    CmdStatus process(uint8_t const *cmd, uint8_t response[64]);
    CmdStatus task(uint8_t response[64]);
protected:
    CmdStatus initPin(uint8_t const *cmd);
    CmdStatus setPin(uint8_t const *cmd);
    CmdStatus getPin(uint8_t const *cmd, uint8_t response[64]);
    CmdStatus setIrq(uint8_t const *cmd);
    CmdStatus getIrq(uint8_t const *cmd, uint8_t response[64]);
private:
    repeating_timer_t _debounceTimer;

    CmdStatus initPinGpio(uint8_t const *cmd);
    CmdStatus initPinExp(uint8_t const *cmd);
    CmdStatus setPinGpio(uint8_t const *cmd);
    CmdStatus setPinExp(uint8_t const *cmd);
    CmdStatus getPinGpio(uint8_t const *cmd, uint8_t response[64]);
    CmdStatus getPinExp(uint8_t const *cmd, uint8_t response[64]);

#ifdef PCA9555_0_ENABLED
    pca9555 exp0{(PCA9555_0_I2C_INSTANCE == 0 ? i2c0 : i2c1), PCA9555_0_ID, PCA9555_0_INT_GPIO};
#endif
#ifdef PCA9555_1_ENABLED
    pca9555 exp1{(PCA9555_1_I2C_INSTANCE == 0 ? i2c0 : i2c1), PCA9555_1_ID, PCA9555_1_INT_GPIO};
#endif
};

#endif
