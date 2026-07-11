import radio_df
import radio_df.music


def test_music_skeleton_shape():
    spectrum = radio_df.music.music(None, 1, 4)
    assert spectrum.shape == (360,)
