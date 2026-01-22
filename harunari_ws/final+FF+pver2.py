def compute_cmd(self, target, actual):
    error = target - actual

    ff_cmd = int(-target * self.ff_gain)
    p_cmd  = int(-self.Kp * error * 1000)

    cmd = ff_cmd + p_cmd
    cmd = max(min(cmd, self.MAX_CMD), -self.MAX_CMD)

    return cmd, error
