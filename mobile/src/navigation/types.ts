export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type AppStackParamList = {
  MainTabs: undefined;
  Settings: undefined;
  WorkoutLog: undefined;
  LogWorkout: undefined;
  WorkoutDetail: { workoutId: string };
  EditWorkout: { workoutId: string };
};

export type TabParamList = {
  Teams: undefined;
  Stats: undefined;
  Profile: undefined;
};
