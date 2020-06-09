
## Background
Every year, I accept an annual challenge. In past years, this has been anything from running a marathon (2007) or 1/2 ironman (2010), to a food challenge (2012), or even trying out for American Ninja Warrior (2018). According to [StrengthsFinder](https://www.gallup.com/cliftonstrengths/en/252137/home.aspx), Learner is my #1 strength, so the goal is to continually push myself into new areas so I can continue to learn and grow.

This year (2020), I've accepted the challenge to build an Automated Foosball Table. This will allow me to gain working knowledge of Python, OpenCV (computer vision), and Artificial Intelligence (AI). In addition, it will allow me to brush up on other areas including robotics, physics, mechanical engineering, and programming. As an added benefit, it will also allow my oldest daughter (6 yr) to be able to play foosball any time she wants, even when I'm not available.

The end goal is to complete a working prototype of a foosball table that is capable of beating a human at the game of foosball by midnight on Dec 31, 2020.


## Setup
The basic setup will be a foosball table and a camera connected to a [Raspberry Pi](https://www.raspberrypi.org/). This will allow for image detection to be able to detect and track the position of the table, foosball, and players at all times. This information will serve as input to the main script, which in turn will control motors connected to each foosball rod on one side of the table. Each rod will have two motors attached (linear and rotational) which will control the players (blocking, kicking, etc).

The main AI script will also output a "preview" of what the computer sees in real time:

![Screenshot](media/screenshot.png)


## Strategy
Part of the challenge requires determining how the main AI script should respond, based on the current conditions of the game. This requires the following 3 assumptions:

```
* The computer can detect and track the table, foosball, and players at all times.
* The computer is able to move both motors (linear and rotational) on all 4 rows simultaneously.
* The foosball can be controlled by, at most, one row at a time.
```

Assuming these 3 assumptions are met, the Automated Foosball Table will first attempt a DEFENSIVE posture, followed by an OFFENSIVE posture, followed by a HOLDING pattern.

A more detailed version of this strategy can be found [here](media/strategy.pdf).
