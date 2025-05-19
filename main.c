#include "extra/neslib.h"
#include "extra/nesplus.h"

// general purpose vars
static unsigned char i, j, spr;

// total number of balls on the screen
#define BALLS_MAX 64
#define SPR_BALL 64

// balls parameters
static unsigned char ball_x[BALLS_MAX], ball_y[BALLS_MAX], ball_dx[BALLS_MAX], ball_dy[BALLS_MAX];

void main(void)
{
	pal_spr(palette_0);
	ppu_on_all();

	// initialize balls parameters
	for (i = 0; i < BALLS_MAX; ++i)
	{
		// starting coordinates
		ball_x[i] = rand8();
		ball_y[i] = rand8();

		// direction bits
		j = rand8();

		// horizontal speed -3..-3, excluding 0
		spr = 1 + (rand8() % 3);
		ball_dx[i] = j & 1 ? -spr : spr;

		// vertical speed
		spr = 1 + (rand8() % 3);
		ball_dy[i] = j & 2 ? -spr : spr;
	}

	// main loop
	while (TRUE)
	{
		spr = 0;

		for (i = 0; i < BALLS_MAX; ++i)
		{
			// set a sprite for current ball
			spr = oam_spr(ball_x[i], ball_y[i], SPR_BALL, i & 3, spr);

			// move the ball
			ball_x[i] += ball_dx[i];
			ball_y[i] += ball_dy[i];

			// bounce the ball off the edges
			if (ball_x[i] >= (SCREEN_WIDTH - 8))
				ball_dx[i] = -ball_dx[i];

			if (ball_y[i] >= (SCREEN_HEIGHT - 8))
				ball_dy[i] = -ball_dy[i];
		}

		ppu_wait_frame();
	}
}