#include "palettes.h"

#define SCREEN_HEIGHT 240
#define SCREEN_WIDTH 256

void sfx_chirp()
{
    *((unsigned char *)0x4000) = 0x0f;
    *((unsigned char *)0x4001) = 0xab;
    *((unsigned char *)0x4003) = 0x01;
}

void sfx_noise()
{
    *((unsigned char *)0x400c) = 0x0f;
    *((unsigned char *)0x400e) = 0x0c;
    *((unsigned char *)0x400e) = 0x00;
}

void sfx_beep()
{
    *((unsigned char *)0x4000) = 0x0f;
    *((unsigned char *)0x4001) = 0xab;
    *((unsigned char *)0x4003) = 0x01;
}