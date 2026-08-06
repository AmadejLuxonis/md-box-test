#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "pico/stdio.h"
#include "pca9555.h"
#include "board_config.h"

/**
 * @brief Construct a new pca9555::pca9555 object
 *
 * @param address
 * @param int_pin_num set to zero if polling
 */

pca9555::pca9555(i2c_inst_t * i2c_instance, uint8_t id, uint8_t int_pin_num)
{
  this->i2c_instance = i2c_instance;

  if (id == PCA9555_0_ID) {
    i2c_init((PCA9555_0_I2C_INSTANCE == 0 ? i2c0 : i2c1), 100 * 1000);
    gpio_set_function(PCA9555_0_I2C_SDA_GPIO, GPIO_FUNC_I2C);
    gpio_set_function(PCA9555_0_I2C_SCL_GPIO, GPIO_FUNC_I2C);
    gpio_pull_up(PCA9555_0_I2C_SDA_GPIO);
    gpio_pull_up(PCA9555_0_I2C_SCL_GPIO);

    this->address = PCA9555_0_I2C_ADDRESS;
  } else {
    i2c_init((PCA9555_1_I2C_INSTANCE == 0 ? i2c0 : i2c1), 100 * 1000);
    gpio_set_function(PCA9555_1_I2C_SDA_GPIO, GPIO_FUNC_I2C);
    gpio_set_function(PCA9555_1_I2C_SCL_GPIO, GPIO_FUNC_I2C);
    gpio_pull_up(PCA9555_1_I2C_SDA_GPIO);
    gpio_pull_up(PCA9555_1_I2C_SCL_GPIO);

    this->address = pca9555Exists((PCA9555_1_I2C_INSTANCE == 0 ? i2c0 : i2c1),
    PCA9555_1_I2C_ADDRESS) ? PCA9555_1_I2C_ADDRESS : PCA9555_1_I2C_ADDRESS_ALTERNATE;
  }

  if (int_pin_num > 0)
  {
    this->int_pin_num = int_pin_num;
    gpio_init(int_pin_num);
    gpio_set_dir(int_pin_num, false);
    gpio_is_pulled_up(int_pin_num);
  } else {
    int_pin_num = 0;
  }
}

bool pca9555::pca9555Exists(i2c_inst_t *i2c, uint8_t address) {
    constexpr uint8_t inputPort0Register = 0x00;
    uint8_t value = 0;

    // Set the PCA9555 register pointer.
    const int writeResult = i2c_write_timeout_us(
        i2c,
        address,
        &inputPort0Register,
        1,
        true,       // Keep control of the bus for the following read.
        1000
    );

    if(writeResult != 1) {
        return false;
    }

    // Verify that the device responds with readable register data.
    const int readResult = i2c_read_timeout_us(
        i2c,
        address,
        &value,
        1,
        false,
        1000
    );

    return readResult == 1;
}

/**
 * @brief Set pins as input or output
 *
 * @param config_ports
 */
void pca9555::pin_mode(config_ports_t *config_ports)
{
  uint8_t reg_config[2] = {config_ports->config_port0.all, config_ports->config_port1.all};
  twi_write(this->address, cp_0, reg_config, 2);
  read_input(); // to clear interrupts (if any)
}

/**
 * @brief Set pins as input or output
 *
 * @param config_ports
 */
void pca9555::set_output(output_ports_t *output_ports)
{
  uint8_t reg_config[2] = {output_ports->config_port0.all, output_ports->config_port1.all};
  twi_write(this->address, op_0, reg_config, 2);
  read_input();
}

/**
 * Modify just one pin as input or output
 */
void pca9555::set_pin_mode(uint8_t pin, uint8_t mode) {
  uint16_t cp01reg = twi_read(this->address, cp_0);
  if(mode) {
    cp01reg |= 1<<pin;
  } else {
    cp01reg &= ~(1<<pin);
  }
  twi_write(this->address, cp_0, (uint8_t*) &cp01reg, 2);
}

/**
 * Modify just one pin as high or low
 */
void pca9555::set_pin_value(uint8_t pin, uint8_t value) {
  uint16_t op01reg = twi_read(this->address, op_0);
  if(value) {
    op01reg |= 1<<pin;
  } else {
    op01reg &= ~(1<<pin);
  }
  twi_write(this->address, op_0, (uint8_t*) &op01reg, 2);
}

/**
 * @brief set polarity of the pins
 *
 * @param pol_ports
 */
void pca9555::set_polarity(polarity_ports_t *pol_ports)
{
  uint8_t pol_config[2] = {pol_ports->polarity_port0.all, pol_ports->polarity_port1.all};
  twi_write(address, pi_0, pol_config, 2);
}

/**
 * @brief read value of the input regs
 *
 * @return uint16_t
 */
uint16_t pca9555::read_input()
{
  return twi_read(address, ip_0);
}

/**
 * @name twi_read(uint8_t address, uint8_t reg)
 * @param address
 * @param reg
 * @return uint16_t
 */
uint16_t pca9555::twi_read(uint8_t address, uint8_t reg)
{
  uint8_t _inputData[2];
  word_u words_;
  _error = i2c_write_blocking(i2c_instance, address, &reg, 1, true);
  _error = i2c_read_blocking(i2c_instance, address, (uint8_t *)&_inputData, 2, false);
  // printf("%d", _error);
  words_.byte[0] = _inputData[0];
  words_.byte[1] = _inputData[1];

  return words_.word;
}

/**
 * @name twi_write(uint8_t address, uint8_t reg, uint8_t value, uint8_t len)
 * @param address Address of I2C chip
 * @param reg    register to write to
 * @param value    value to write to register
 * @param len length of data being sent
 * Write the value given to the register set to selected chip.
 */
void pca9555::twi_write(uint8_t address, uint8_t reg, uint8_t *value, uint8_t len)
{
  uint8_t buffer[3];

  buffer[0] = reg;

  for(int i = 0; i < len; i++)
      buffer[i+1] = value[i];

  _error = i2c_write_blocking(i2c_instance, address, buffer, len + 1, false);
}
