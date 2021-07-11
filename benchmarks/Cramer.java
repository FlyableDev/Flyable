import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Cramer {

    public static void copy_matrix(List<List<Float>> a, List<List<Float>> m) {
        for(int i = 0; i < a.size(); i++) {
            List<Float> list = new ArrayList<>();
            for(int j = 0; j < a.get(0).size(); j++) {
                list.add(a.get(i).get(j));
            }
            m.add(list);
        }
    }

    public static float cofactor(List<List<Float>> a, int i) {
        List<List<Float>> m = new ArrayList<>();
        copy_matrix(a, m);
        m.remove(0);
        for(int j = 0; j < m.size(); j++){
            m.get(j).remove(i);
        }
        return (float) Math.pow(-1, i) * det(m);
    }

    public static float det(List<List<Float>> a) {
        if(a.size() == 2){
            return a.get(0).get(0) * a.get(1).get(1) - a.get(0).get(1) * a.get(1).get(0);
        }
        else{
            float result = 0;
            for (int i = 0; i < a.size(); i++){
                result += a.get(0).get(i) * cofactor(a, i);
            }
            return result;
        }
    }

    public static void main(String[] args) {

        List<List<Float>> matrix = new ArrayList<>();
        matrix.add(Arrays.asList(0f, 5f, 4f, 8f, 6f, 10f, 69f, 301f, 24f));
        matrix.add(Arrays.asList(5f, 6f, 19f, 1f, 75f, 47f, 456f, 85f, 65f));
        matrix.add(Arrays.asList(37f, 1f, 11f, 83f, 5f, 7f, 78f, 3f, 36f));
        matrix.add(Arrays.asList(5f, 9f, 87f, 52f, 41f, 9f, 56f, 6f, 87f));
        matrix.add(Arrays.asList(97f, 53f, 1f, 65f, 3f, 103f, 82f, 78f, 3f));
        matrix.add(Arrays.asList(45f, 13f, 2f, 25f, 5f, 789f, 19f, 98f, 189f));
        matrix.add(Arrays.asList(23f, 58f, 76f, 91f, 46f, 2f, 356f, 62f, 963f));
        matrix.add(Arrays.asList(58f, 6f, 358f, 45f, 42f, 598f, 7f, 8f, 12f));
        matrix.add(Arrays.asList(350f, 20f, 60f, 40f, 90f, 70f, 110f, 13f, 78f));

        List<Float> vector = new ArrayList<>();
        vector = Arrays.asList(4f, 86f, 32f, 56f, 89f, 2f, 103f, 28f, 110f);

        float determinant = det(matrix);

        List<Float> x_i = new ArrayList<>();

        for (int i = 0; i < matrix.size(); i++){
            List<List<Float>> matrix_i = new ArrayList<>();
            copy_matrix(matrix, matrix_i);
            for (int j = 0; j < matrix.size(); j++){
                matrix_i.get(i).set(j, vector.get(j));
            }
            x_i.add(det(matrix_i)/determinant);
        }
        System.out.println(x_i);
    }
}